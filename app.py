from clams import ClamsApp, Restifier, AppMetadata

from tesseract_utils import *

__version__ = 0.1


class OCR(ClamsApp):
    def _appmetadata(self) -> AppMetadata:
        metadata = AppMetadata(
            name="Tesseract OCR Wrapper",
            description="This tool applies Tesseract OCR to a video or"
            "image and generates text boxes and OCR results.",
            app_version=__version__,
            app_license='MIT',
            analyzer_license='apache',
            url="https://github.com/clamsproject/app-tesseractocr-wrapper", 
            identifier=f"http://apps.clams.ai/tesseract/{__version__}",
        )
        metadata.add_input(DocumentTypes.VideoDocument)
        metadata.add_input(AnnotationTypes.BoundingBox, required=False, boxType='text')
        
        metadata.add_output(DocumentTypes.TextDocument)
        metadata.add_output(AnnotationTypes.BoundingBox)
        metadata.add_output(AnnotationTypes.Alignment)
        
        metadata.add_parameter(name='boxType', type='string', 
                               description='When set, use exising "text"-typed ``BoundingBox`` annotations '
                                           'and run tesseract only on those regions, instead of entire frames.', 
                               default=' ')
        # metadata.add_parameter(name='frame_type', type='string',
        #                        description='When set only apply tesseract to frames annotated with a given frame type',
        #                        default='')
        return metadata

    
    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        self.sign_view(new_view, self.get_configuration(**kwargs))
        new_view.new_contain(DocumentTypes.TextDocument)
        box_type = kwargs.pop("boxType").strip() if "boxType" in kwargs else None
        if box_type:
            mmif_obj = box_ocr(mmif_obj, new_view, box_type, **kwargs)
        else:
            mmif_obj = full_ocr(mmif_obj, new_view, **kwargs)
        return mmif_obj


if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()