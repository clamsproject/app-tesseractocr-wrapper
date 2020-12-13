from typing import Optional, List, Tuple, Dict
import cv2
import pytesseract
import json
import collections
import numpy as np
from mmif.vocabulary import DocumentTypes, AnnotationTypes
from mmif import Mmif, View, Annotation

BB = collections.namedtuple("BoundingBox", "conf left top width height text")
SAMPLE_RATIO = 30
BOX_THRESHOLD = 90
TARGET_FRAME_TYPE = "slate"


def generate_text_and_boxes(image: np.array, view:View, frame_num=None, threshold: int = BOX_THRESHOLD) -> View:
    tess_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    cleaned_results = []
    for box in zip(
        tess_result["conf"],
        tess_result["left"],
        tess_result["top"],
        tess_result["width"],
        tess_result["height"],
        tess_result["text"],
    ):
        if type(box[0]) is int and box[0] > threshold and len(box[5].strip()) > 0:
            cleaned_results.append(
                BB(
                    conf=box[0],
                    left=box[1],
                    top=box[2],
                    width=box[3],
                    height=box[4],
                    text=box[5],
                )
            )
    for _id, box in enumerate(cleaned_results):
        if frame_num:
            _id = f"{frame_num}_{_id}"
        bb_annotation = view.new_annotation(f"bb{_id}", AnnotationTypes.BoundingBox)
        bb_annotation.add_property(
            "coordinates",
            ##todo 2020-10-23 kelleylynch property value is restricted to string, should this be a list of list of ints?
            f"{[[box.left, box.top], [box.left, box.top - box.height], [box.left + box.width, box.top], [box.left + box.width, box.top - box.height]]}",
        )
        bb_annotation.add_property("boxType", "text")
        if frame_num:
            bb_annotation.add_property("frame", frame_num)
        td_annotation = view.new_annotation(f"td{_id}", DocumentTypes.TextDocument)
        td_annotation.add_property("text", {"@value": box.text, "@language":"en"})
        align_annotation = view.new_annotation(f"a{_id}", AnnotationTypes.Alignment)
        align_annotation.add_property("source", f"bb{_id}")
        align_annotation.add_property("target", f"td{_id}")
    return view


def add_ocr_and_align(image: np.array, new_view: View, align_id:str, bb_annotations: List[Annotation], frame_num=None) -> View:
    """
    This function applies tesseract to bounding box regions of an image and adds the results to a view with alignment
    annotations linking the generated text documents to the bounding box annotations designating the region
    containing text.
    :param image:
    :param new_view: view to add annotations to
    :param align_id: id of view containing bounding box annotations
    :param bb_annotations: list of annotations containing coordinates of text candidates
    :param frame_num, frame number of the target image
    :return: View containing aligned text document annotations
    """
    for _id, bb_annotation in enumerate(bb_annotations):
        if frame_num:
            _id = f"{frame_num}_{_id}"
        coordinates = json.loads(bb_annotation.properties["coordinates"])
        x0, y0 = coordinates[0]
        x1, y1 = coordinates[3]
        subimage = image[max(0, y0-10):min(y1, image.shape[0]),
                   max(0, x0):min(x1+10, image.shape[1])]
        text_content = pytesseract.image_to_string(subimage) ##todo 2020-10-29 kelleylynch add config here
        tdoc_annotation = new_view.new_annotation(f"td{_id}", DocumentTypes.TextDocument)
        tdoc_annotation.add_property("text", str({"@value": text_content}))
        align_annotation = new_view.new_annotation(f"a{_id}", AnnotationTypes.Alignment)
        align_annotation.add_property("source", f"{align_id}:{bb_annotation.id}")
        align_annotation.add_property("target", tdoc_annotation.id)
    return new_view


def get_text_bb_view(mmif: Mmif) -> Optional[View]:
    for bb_view in mmif.get_all_views_contain(AnnotationTypes.BoundingBox):
        for bb_annotation in filter(lambda x: x.at_type == AnnotationTypes.BoundingBox.value, bb_view.annotations):
            if bb_annotation.properties["boxType"] == "text":
                return bb_view
    return None


def build_target_timeframes(mmif: Mmif, target_type: str) -> Dict[Tuple[str, str], Tuple[int, int]]:
    ##todo 2020-11-01 kelleylynch should this get timeframes from across multiple views?
    result_dict = {}
    for view in mmif.get_all_views_contain(AnnotationTypes.TimeFrame.value):
        for annotation in view.annotations:
            if annotation.properties["frameType"] == target_type:
                if annotation.properties["unit"] == "frame": ##todo 2020-11-01 kelleylynch make this work for other units
                    result_dict[(view.id, annotation.id)] = (annotation.properties["start"], annotation.properties["end"])
    return result_dict


def build_frame_box_dict(view: View):
    annotation_dict = collections.defaultdict(list)
    for annotation in view.get_annotations(AnnotationTypes.Alignment):
        source = get_annotation_by_id(view, annotation.properties["source"])
        target = get_annotation_by_id(view, annotation.properties["target"])
        if source.at_type == AnnotationTypes.TimePoint.value and target.at_type == AnnotationTypes.BoundingBox.value and target.properties["boxType"] == "text":
            if source.properties["unit"] != "frame":
                raise NotImplementedError ##todo 2020-10-29 kelleylynch handle units other than frame
            annotation_dict[source.properties["point"]].append(target)
    return annotation_dict


def get_annotation_by_id(view: View, id: str) -> Annotation:
    return [anno for anno in view.annotations if anno.id == id][0]


def run_video_tesseract(mmif: Mmif, view:View) -> Mmif:
    cap = cv2.VideoCapture(mmif.get_document_location(DocumentTypes.VideoDocument))
    for ann_type in [AnnotationTypes.BoundingBox, DocumentTypes.TextDocument, AnnotationTypes.Alignment]:
        contain = view.new_contain(ann_type)
        contain.producer = "app-tesseractocr-wrapper" #todo de-hardcode this
    counter = 0
    if TARGET_FRAME_TYPE:
        target_timeframes = build_target_timeframes(mmif, TARGET_FRAME_TYPE)
        for ids, framenums in target_timeframes.items():
            target_fnum = (framenums[0]+framenums[1])//2
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_fnum)
            ret, frame = cap.read()
            # todo 2020-11-01 kelleylynch right now we're just annotating the middle frame from each frame range, maybe this should be set with a param
            view = generate_text_and_boxes(frame, view, target_fnum)
            ##todo 2020-11-01 kelleylynch add alignment annotation to align between generated boxes and slate annotation
    else:
        while cap.isOpened():
            ret, f = cap.read()
            if not ret:
                break
            if counter % SAMPLE_RATIO == 0:
                generate_text_and_boxes(image=f, view=view, frame_num=counter)
            counter += 1
    return mmif


def run_image_tesseract(mmif: Mmif, view:View) -> Mmif:
    image = cv2.imread(mmif.get_document_location(DocumentTypes.ImageDocument))
    generate_text_and_boxes(image, view)
    return mmif


def run_aligned_video(mmif:Mmif, new_view:View, text_bb_view: View) -> Mmif:
    cap = cv2.VideoCapture(mmif.get_document_location(DocumentTypes.VideoDocument.value))
    annotation_dict = build_frame_box_dict(text_bb_view)
    #sort the dict on the frame number keys
    od = collections.OrderedDict(sorted(annotation_dict.items()))
    for frame_num, annotation_list in od.items():
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        new_view = add_ocr_and_align(frame, new_view, text_bb_view.id, annotation_list, frame_num)
    return mmif


def run_aligned_image(mmif: Mmif, new_view:View, text_bb_view: View) -> Mmif:
    image = cv2.imread(mmif.get_document_location(DocumentTypes.ImageDocument.value))
    new_view = add_ocr_and_align(image, new_view, text_bb_view.id, text_bb_view.get_annotations(AnnotationTypes.BoundingBox, boxType="text"))
    return mmif
