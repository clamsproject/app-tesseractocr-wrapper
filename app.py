from clams.serve import ClamsApp
from clams.restify import Restifier

from tesseract_utils import *

APP_VERSION = 0.1


class OCR(ClamsApp):
    def setupmetadata(self):
        metadata = {
            "name": "Tesseract OCR",
            "description": "This tool applies Tesseract OCR to an "
            "image and generates text boxes and OCR result.",
            "vendor": "Team CLAMS",
            "iri": f"http://mmif.clams.ai/apps/tesseract/{APP_VERSION}",
            "requires": [DocumentTypes.ImageDocument.value, DocumentTypes.VideoDocument.value],
            "produces": [
                AnnotationTypes.BoundingBox.value,
                AnnotationTypes.Alignment.value,
                DocumentTypes.TextDocument.value,
            ],
        }
        return metadata

    def sniff(self, mmif): # todo 2020-12-13 kelleylynch implement sniff
        # this mock-up method always returns true
        return True

    def annotate(self, mmif: Mmif) -> str:
        """
        :param mmif: this mmif could contain images or video, with or without preannotated text boxes
        :return: annotated mmif as string
        """
        new_view = mmif.new_view()
        new_view.metadata['app'] = self.metadata["iri"]

        if mmif.get_documents_by_type(DocumentTypes.VideoDocument.value):
            mmif = self.annotate_video_mmif(mmif, new_view)
        elif mmif.get_documents_by_type(DocumentTypes.ImageDocument.value):
            mmif = self.annotate_image_mmif(mmif, new_view)
        else:
            raise Exception("Mmif missing valid document type.")
        return str(mmif)

    @staticmethod
    def annotate_image_mmif(mmif: Mmif, view: View) -> Mmif:
        """
        This method applies tesseract to regions of an image, if text box annotations exist, those boxes are
        used, otherwise bounding boxes are generated using tesseract localization.
        :return: annotated Mmif
        """
        text_bb = get_text_bb_view(mmif)
        if text_bb:
            mmif = run_aligned_image(mmif, view, text_bb)
        else:
            mmif = run_image_tesseract(mmif, view)
        return mmif

    @staticmethod
    def annotate_video_mmif(mmif: Mmif, view:View) -> Mmif:
        text_bb = get_text_bb_view(mmif)
        if text_bb:
            mmif = run_aligned_video(mmif, view, text_bb)
        else:
            mmif = run_video_tesseract(mmif, view)
        return mmif


if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()
