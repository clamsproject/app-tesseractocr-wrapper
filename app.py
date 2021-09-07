from clams import ClamsApp, Restifier, AppMetadata

from tesseract_utils import *

APP_VERSION = 0.1


class OCR(ClamsApp):
    def _appmetadata(self):
        metadata = {
            "name": "Tesseract OCR",
            "description": "This tool applies Tesseract OCR to a video or"
            "image and generates text boxes and OCR results.",
            "app_version": APP_VERSION,
            "license": "MIT",
            # "app_license":"",
            # "analyzer_version":"",
            # "analyzer_license":"",
            "identifier": f"http://mmif.clams.ai/apps/tesseract/{APP_VERSION}",
            "input": [
                {
                    "@type": DocumentTypes.ImageDocument,
                    "required": False,
                },
                {
                    "@type": DocumentTypes.VideoDocument,
                    "required": False,
                },  # todo are both of these really false?
            ],
            "output": [
                {
                    "@type": AnnotationTypes.BoundingBox,
                    "properties": {"frameType": "string"},
                },
                {"@type": AnnotationTypes.Alignment},
                {"@type": DocumentTypes.TextDocument},
            ],
        }
        return AppMetadata(**metadata)

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        config = self.get_configuration(**kwargs)
        self.sign_view(new_view, config)
        new_view.new_contain(DocumentTypes.TextDocument)
        box_type = kwargs.pop("boxType") if "boxType" in kwargs else None
        if box_type:
            mmif_obj = box_ocr(mmif_obj, new_view, box_type, **kwargs)
        else:
            mmif_obj = full_ocr(mmif_obj, new_view, **kwargs)
        return mmif_obj


if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()