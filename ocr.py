import cv2
import pytesseract

from clams.serve import ClamApp
from clams.serialize import *
from clams.vocab import AnnotationTypes
from clams.vocab import MediaTypes
from clams.restify import Restifier


class OCR(ClamApp):

    def appmetadata(self):
        metadata = {"name": "Tesseract OCR",
                    "description": "This tool applies Tesseract OCR to the entire video.",
                    "vendor": "Team CLAMS",
                    "requires": [MediaTypes.V],
                    "produces": [AnnotationTypes.OCR]}
        return metadata

    def sniff(self, mmif):
        # this mock-up method always returns true
        return True

    def annotate(self, mmif_json):
        mmif = Mmif(mmif_json)
        video_filename = mmif.get_medium_location(MediaTypes.V)
        ocr_output = self.run_ocr(video_filename, mmif_json) #ocr_output is a list of frame number, text pairs

        new_view = mmif.new_view()
        contain = new_view.new_contain(AnnotationTypes.OCR)
        contain.producer = self.__class__

        for int_id, (start_frame, text) in enumerate(ocr_output):
            annotation = new_view.new_annotation(int_id)
            annotation.start = str(start_frame)
            annotation.end = str(start_frame)  # since we're treating each frame individually for now, start and end are the same
            annotation.feature = {'text':text}
            annotation.attype = AnnotationTypes.OCR

        for contain in new_view.contains.keys():
            mmif.contains.update({contain: new_view.id})
        return mmif

    @staticmethod
    def run_ocr(video_filename, mmif): # mmif here will be used for filtering out frames/
        #apply tesseract ocr to frames
        sample_ratio = 60

        def process_image(f):
            proc = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            # proc = cv2.threshold(proc, 0, 255,
            #                      cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            proc = cv2.medianBlur(proc, 5)
            return proc

        cap = cv2.VideoCapture(video_filename)
        counter = 0
        ocr_result = []

        while cap.isOpened():
            ret, f = cap.read()
            if not ret:
                break
            if counter % sample_ratio == 0:
                processed_frame = process_image(f)
                result = pytesseract.image_to_string(processed_frame)
                if len(result) > 5:
                    ocr_result.append((counter, result))
            counter += 1
        return ocr_result

if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()

