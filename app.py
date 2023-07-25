import argparse
import logging
import warnings

import cv2
from PIL import Image
from clams import ClamsApp, Restifier, AppMetadata
from mmif import DocumentTypes, Mmif, AnnotationTypes
from mmif.utils import video_document_helper as vdh

from tesseract_utils import *


class OCR(ClamsApp):
    def _appmetadata(self) -> AppMetadata:
        """See metadata.py"""
        pass

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        config = self.get_configuration(**kwargs)

        tess_wrapper = Tesseract()
        tess_wrapper.BOX_THRESHOLD = config.get("threshold", 90)
        tess_wrapper.PSM = config.get("psm", None)
        tess_wrapper.OEM = config.get("oem", None)
        tess_wrapper.CHAR_WHITELIST = config.get("char_whitelist", None)

        vds = mmif_obj.get_documents_by_type(DocumentTypes.VideoDocument)
        if vds:
            videoObj = vdh.capture(vds[0])
        else:
            warnings.warn("No video document found in the input MMIF.")
            return mmif_obj
        # TODO (krim @ 7/25/23): add a proper frame_type filtering
        target_time_segments = [0, int(vds[0].get_property('frameCount'))]
        for textbox_view in mmif_obj.get_all_views_contain(AnnotationTypes.BoundingBox):
            for box in textbox_view.get_annotations(AnnotationTypes.BoundingBox, boxType="text"):
                frame_number = vdh.convert_timepoint(mmif_obj, box, 'frame')
                if not (target_time_segments[0] <= frame_number < target_time_segments[1]):
                    continue
                videoObj.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                _, im = videoObj.read()
                if im is not None:
                    im = Image.fromarray(im.astype("uint8"), 'RGB')
                    (top_left_x, top_left_y), _, _, (bottom_right_x, bottom_right_y) = box.get_property("coordinates")
                    cropped = im.crop((top_left_x, top_left_y, bottom_right_x, bottom_right_y))
                    label = tess_wrapper.image_to_string(cropped).strip()

                    self.logger.debug(f"OCR prediction: {label}")
                    text_document = new_view.new_textdocument(' '.join(label))
                    alignment = new_view.new_annotation(AnnotationTypes.Alignment)
                    alignment.add_property("target", text_document.id)
                    alignment.add_property("source", f'{textbox_view.id}:{box.id}')
        return mmif_obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="5000", help="set port to listen")
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # add more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    app = OCR()

    http_app = Restifier(app, port=int(parsed_args.port))
    # for running the application in production mode
    if parsed_args.production:
        http_app.serve_production()
    # development mode
    else:
        app.logger.setLevel(logging.DEBUG)
        http_app.run()
