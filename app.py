from clams.app import ClamsApp
from clams.restify import Restifier

from tesseract_utils import *

APP_VERSION = 0.1


class OCR(ClamsApp):
    def _appmetadata(self):
        metadata = {
            "name": "Tesseract OCR",
            "description": "This tool applies Tesseract OCR to an "
            "image and generates text boxes and OCR result.",
            "identifier": f"http://mmif.clams.ai/apps/tesseract/{APP_VERSION}",
            "input": [
            { "@type": DocumentTypes.ImageDocument.value,
            "required":False,
            },
            {"@type":DocumentTypes.VideoDocument.value,
            "required":False} # todo are both of these really false?
            ],
            "output": [
                {"@type":AnnotationTypes.BoundingBox.value, "properties":{"frameType":"string"}},
                {"@type":AnnotationTypes.Alignment.value},
                {"@type":DocumentTypes.TextDocument.value},
            ],
        }
        return metadata

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        config = self.get_configuration(**kwargs)
        self.sign_view(v, config)
        new_view.new_contain(DocumentTypes.TextDocument)
        box_type = kwargs.pop('boxType') if 'boxType' in kwargs else None
        if box_type:
            mmif_obj = box_ocr(mmif_obj, new_view, box_type, **kwargs)
        else:
            mmif_obj = full_ocr(mmif_obj, new_view, **kwargs)
        return mmif_obj


if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()
