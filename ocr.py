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

    def annotate(self, mmif):
        if type(mmif) is not Mmif:
            mmif = Mmif(mmif)
        video_filename = mmif.get_medium_location(MediaTypes.V)

        ocr_output = []
        ##check to see if there are text boxes in the mmif
        if AnnotationTypes.TBOX in mmif.contains.keys():
            ocr_output = self.filtered_ocr(video_filename, mmif)
        else:
            ocr_output = self.run_ocr(video_filename, mmif) #ocr_output is a list of frame number, [(text, target)] pairs

        new_view = mmif.new_view()
        contain = new_view.new_contain(AnnotationTypes.OCR)
        contain.producer = self.__class__

        for int_id, (start_frame, text_target_list) in enumerate(ocr_output):
            annotation = new_view.new_annotation(int_id)
            annotation.start = str(start_frame)
            annotation.end = str(start_frame)  # since we're treating each frame individually for now, start and end are the same
            annotation.attype = AnnotationTypes.OCR

            for (text, target) in text_target_list:
                annotation.feature = {'text':text, 'target':target}

        for contain in new_view.contains.keys():
            mmif.contains.update({contain: new_view.id})
        return mmif


    @staticmethod
    def filtered_ocr(video_filename, mmif):
        ''''''
        tb_view = mmif.get_view_contains(AnnotationTypes.TBOX)
        view_id = tb_view["id"]
        tb_annotations = tb_view["annotations"]
        cap = cv2.VideoCapture(video_filename)
        ocr_result = []

        def process_image(f):
            proc = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            # proc = cv2.threshold(proc, 0, 255,
            #                      cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            proc = cv2.medianBlur(proc, 5)
            return proc

        for annotation in tb_annotations:
            ## {"start": "360", "end": "360", "feature": {"boxes": [[466, 459, 587, 504]]}, "id": 0, "attype": "text-box"}
            aid = annotation["id"]
            framenum = int(annotation["start"])

            cap.set(cv2.CAP_PROP_POS_FRAMES, framenum)
            ret, frame = cap.read()
            processed_frame = process_image(frame)
            box_targets = annotation["feature"]["boxes"]
            results = []
            print (processed_frame.shape)
            for i, box in enumerate(box_targets):
                # get crop of box
                # add (text_from_crop, view_id:annotation_id:i)
                crop = processed_frame[box[1]:box[3], box[0]:box[2]]
                try:
                    txt = pytesseract.image_to_string(crop)
                    if len(txt) > 1: #TODO revisit this to see if the east boxes are just empty
                        results.append((txt, ":".join([view_id, str(aid), str(i)])))
                except Exception as e:
                    print ("error on {}".format(box))
            ocr_result.append((framenum, results))
        # ocr_result is a list of frame number, [(text, target)] pairs
        return ocr_result

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
                    ocr_result.append((counter, [(result, "frame")]))
            counter += 1
        return ocr_result

if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()

