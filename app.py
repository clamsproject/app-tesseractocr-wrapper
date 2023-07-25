import argparse
import bisect
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
        tess_wrapper.PSM = config.get("psm")

        vds = mmif_obj.get_documents_by_type(DocumentTypes.VideoDocument)
        if vds:
            videoObj = vdh.capture(vds[0])
        else:
            warnings.warn("No video document found in the input MMIF.")
            return mmif_obj
        
        # building "valid" time segments from existing TF annotations
        ## collect all TF annotations as time intervals
        target_time_segments = []
        found_time_segments = []
        frame_types = set(config.get("frameType", []))
        frame_types.discard('')
        self.logger.debug(f"frame_types: {frame_types}")
    
        if frame_types:
            for tf_view in mmif_obj.get_all_views_contain(AnnotationTypes.TimeFrame):
                for tf_ann in tf_view.get_annotations(AnnotationTypes.TimeFrame):
                    if tf_ann.get_property('frameType') in frame_types:
                        self.logger.debug(f"found TF: {tf_ann.id} of type {tf_ann.get_property('frameType')}")
                        bisect.insort(found_time_segments, vdh.convert_timeframe(mmif_obj, tf_ann, 'frame'))
        else:
            found_time_segments.append([0, int(vds[0].get_property('frameCount'))])
        # merge any overlapping intervals 
        if found_time_segments:
            target_time_segments.append(found_time_segments[0])
            for i in range(1, len(found_time_segments)):
                if target_time_segments[-1][1] >= found_time_segments[i][0]:
                    if target_time_segments[-1][1] < found_time_segments[i][1]:
                        target_time_segments[-1][1] = found_time_segments[i][1]
                else:
                    target_time_segments.append(found_time_segments[i])
        # these two lists are parallel, and will be used for filtering
        if not target_time_segments:
            warnings.warn(f"No valid TimeFrames of asked types ({frame_types}) found in the input MMIF.")
            return mmif_obj
        target_time_segment_starts, target_time_segment_ends = zip(*target_time_segments)
        
        for textbox_view in mmif_obj.get_all_views_contain(AnnotationTypes.BoundingBox):
            for box in textbox_view.get_annotations(AnnotationTypes.BoundingBox, boxType="text"):
                frame_number = vdh.convert_timepoint(mmif_obj, box, 'frame')
                # filter out any frames that are not in the "valid" time segments
                if bisect.bisect(target_time_segment_starts, frame_number) != bisect.bisect(target_time_segment_ends, frame_number) + 1:
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
