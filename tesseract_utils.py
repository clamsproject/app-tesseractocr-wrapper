from typing import Optional, List, Tuple, Dict
import warnings 

import cv2
import pytesseract
import collections
import numpy as np
from mmif.vocabulary import DocumentTypes, AnnotationTypes
from mmif import Mmif, View, Annotation
from mmif.utils import video_document_helper as vdh

BB = collections.namedtuple("BoundingBox", "conf left top width height text")


class Tesseract:
    def __init__(self):
        self.SAMPLE_RATIO = 30
        self.BOX_THRESHOLD = 90
        self.PSM = None
        self.OEM = None
        self.CHAR_WHITELIST = None
        self.LANG = "eng"

    def get_config(self):
        config = ""
        if self.PSM:
            config += f"--psm {self.PSM} "
        if self.OEM:
            config += f"--oem {self.OEM} "
        if self.CHAR_WHITELIST:
            config += f"-c tessedit_char_whitelist={self.CHAR_WHITELIST} "
        return config

    def image_to_string(self, image):
        return pytesseract.image_to_string(
            image,
            config=self.get_config(),
            lang=self.LANG,
        )

    def image_to_data(self, image):
        tess_result = pytesseract.image_to_data(
            image,
            config=self.get_config(),
            lang=self.LANG,
            output_type=pytesseract.Output.DICT,
        )
        cleaned_results = []
        for box in zip(
            tess_result["conf"],
            tess_result["left"],
            tess_result["top"],
            tess_result["width"],
            tess_result["height"],
            tess_result["text"],
        ):
            if (
                type(box[0]) is int
                and box[0] > self.BOX_THRESHOLD
                and len(box[5].strip()) > 0
            ):
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
        return cleaned_results


tess_wrapper = Tesseract()


def generate_text_and_boxes(image: np.array, view: View, frame_num=None) -> View:
    cleaned_results = tess_wrapper.image_to_data(image)
    for _id, box in enumerate(cleaned_results):
        if frame_num:
            _id = f"{frame_num}_{_id}"
        bb_annotation = view.new_annotation(AnnotationTypes.BoundingBox)
        bb_annotation.add_property(
            "coordinates",
            [
                [box.left, box.top],
                [box.left, box.top + box.height],
                [box.left + box.width, box.top],
                [box.left + box.width, box.top + box.height],
            ],
        )
        bb_annotation.add_property("boxType", "text")
        if frame_num:
            bb_annotation.add_property("timePoint", frame_num)
        td_annotation = view.new_annotation(DocumentTypes.TextDocument)
        td_annotation.properties.text_language = "en"
        td_annotation.properties.text_value = box.text
        align_annotation = view.new_annotation(AnnotationTypes.Alignment)
        align_annotation.add_property("source", bb_annotation.id)
        align_annotation.add_property("target", td_annotation.id)
    return view


def add_ocr_and_align(
    image: np.array,
    new_view: View,
    align_id: str,
    bb_annotations: List[Annotation],
    frame_num=None,
) -> View:
    """
    This function applies tesseract to bounding box regions of an image and adds the results to a view with alignment
    annotations linking the generated text documents to the bounding box annotations designating the region
    containing text.
    :param image:
    :param new_view: view to add annotations to
    :param align_id: id of view containing bounding box annotations, becomes prefix
    :param bb_annotations: list of annotations containing coordinates of text candidates
    :param frame_num, frame number of the target image
    :return: View containing aligned text document annotations
    """
    for _id, bb_annotation in enumerate(bb_annotations):
        if frame_num:
            _id = f"{frame_num}_{_id}"
        coordinates = bb_annotation.get_property('coordinates')
        x0, y0 = coordinates[0]
        x1, y1 = coordinates[3]
        image_crop = image[
            max(0, y0 - 10) : min(y1, image.shape[0]),
            max(0, x0) : min(x1 + 10, image.shape[1]),
        ]
        text_content = tess_wrapper.image_to_string(
            image_crop
        ).strip()
        if text_content:
            td = new_view.new_textdocument(text_content)
            align_annotation = new_view.new_annotation(AnnotationTypes.Alignment)
            align_annotation.add_property("source", f"{align_id}:{bb_annotation.id}")
            align_annotation.add_property("target", td.id)
    return new_view


def build_target_timeframes(
    mmif: Mmif, target_type: Optional[str]
) -> Dict[Tuple[str, str], Tuple[str, str, str]]:
    #TODO: 2020-11-01 kelleylynch should this get timeframes from across multiple views?
    result_dict = {}
    for view in mmif.get_all_views_contain(AnnotationTypes.TimeFrame):
        for annotation in view.annotations:
            if annotation.properties["frameType"] == target_type:
                timeframe_as_frame = vdh.convert_timeframe(mmif, annotation, 'frame')
                result_dict[(view.id, annotation.id)] = (
                timeframe_as_frame[0],
                timeframe_as_frame[1],
                'frame')
                #TODO: 2020-11-01 kelleylynch make this work for other units
    return result_dict


def build_frame_box_dict(view: View, box_type: str):
    annotation_dict = collections.defaultdict(list)
    for annotation in view.get_annotations(
        AnnotationTypes.BoundingBox, boxType=box_type
    ):
        # if annotation.properties["unit"] != "frame":
        #     raise NotImplementedError TODO: 2020-10-29 kelleylynch handle units other than frame
        annotation_dict[annotation.get_property("timePoint")].append(annotation)
    return annotation_dict


def get_annotation_by_id(view: View, id: str) -> Annotation:
    return [anno for anno in view.annotations if anno.id == id][0]


def run_video_tesseract(mmif: Mmif, view: View, **kwargs) -> Mmif:
    document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
    cap = vdh.capture(document)
    view.new_contain(AnnotationTypes.BoundingBox, document=document.id)
    view.new_contain(DocumentTypes.TextDocument)
    view.new_contain(AnnotationTypes.Alignment)
    FRAME_TYPE = kwargs.get("frameType", None)
    counter = 0
    if FRAME_TYPE:
        target_timeframes = build_target_timeframes(mmif, FRAME_TYPE)
        for ids, (start, end, unit) in target_timeframes.items():
            offset = (int(start) + int(end)) // 2
            #TODO: DC 2023-07-21: find a way to leverage vdh helpers here? 
            if unit == "frame":
                cap.set(cv2.CAP_PROP_POS_FRAMES, offset)
            elif unit == "msec":
                cap.set(cv2.CAP_PROP_POS_MSEC, offset)
                offset = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            else:
                raise Exception("invalid timeframe unit")
            ret, frame = cap.read()
            #TODO: 2020-11-01 kelleylynch right now we're just annotating the middle frame from each frame range, 
            # maybe this should be set with a param
            generate_text_and_boxes(frame, view, offset)
    else:
        SAMPLE_RATIO = int(kwargs.get("sampleRatio", 30))
        while cap.isOpened():
            ret, f = cap.read()
            if not ret:
                break
            if counter % SAMPLE_RATIO == 0:
                generate_text_and_boxes(image=f, view=view, frame_num=counter)
            counter += 1
    return mmif


def run_image_tesseract(mmif: Mmif, view: View) -> Mmif:
    image = cv2.imread(mmif.get_document_location(DocumentTypes.ImageDocument))
    generate_text_and_boxes(image, view)
    return mmif


def run_aligned_video(
    mmif: Mmif, new_view: View, bb_views: List[View], box_type: str, valid_frame_list=None #TODO: DC 2023-07-21: valid_frame_list is unused
) -> Mmif:
    document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
    cap = vdh.capture(document)
    for view in bb_views:
        annotation_dict = build_frame_box_dict(view, box_type)
        for frame_num, annotation_list in annotation_dict.items():
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            add_ocr_and_align(frame, new_view, view.id, annotation_list, frame_num)
    return mmif


def run_aligned_image(
    mmif: Mmif, new_view: View, bb_views: List[View], box_type: str
) -> Mmif:
    image = cv2.imread(mmif.get_document_location(DocumentTypes.ImageDocument))
    for view in bb_views:
        add_ocr_and_align(
            image,
            new_view,
            view.id,
            view.get_annotations(AnnotationTypes.BoundingBox, boxType=box_type),
        )
    return mmif


def box_ocr(mmif_obj, new_view, **kwargs):
    tess_wrapper.BOX_THRESHOLD = kwargs["box_threshold"] if "box_threshold" in kwargs else 90
    tess_wrapper.PSM = kwargs["psm"] if "psm" in kwargs else None
    tess_wrapper.OEM = kwargs["oem"] if "oem" in kwargs else None
    tess_wrapper.CHAR_WHITELIST = kwargs["char_whitelist"] if "char_whitelist" in kwargs else None
    FRAME_TYPE = kwargs["frameType"] if "frameType" in kwargs else None #slate, credits, etc
    BOX_TYPE = "text" #TODO: DC 2023-07-21: add a way to actually grab the box type from the annotations 

    views_with_bbox = [
        bb_view
        for bb_view in mmif_obj.get_all_views_contain(AnnotationTypes.BoundingBox)
        if bb_view.get_annotations(AnnotationTypes.BoundingBox, boxType='text')
    ]

    if mmif_obj.get_documents_by_type(DocumentTypes.VideoDocument):
        frame_number_ranges=[(0, 30*60*60*3)]
        #TODO: 2021-03-01 kelleylynch need to handle if there is boxType and frameType
        if FRAME_TYPE:
            views_with_timeframe = [
                tf_view
                for tf_view in mmif_obj.get_all_views_contain(AnnotationTypes.TimeFrame)
                if tf_view.get_annotations(AnnotationTypes.TimeFrame, frameType=FRAME_TYPE)
            ]
            frame_number_ranges = [
                (tf_annotation.properties["start"], tf_annotation.properties["end"])
                for tf_view in views_with_timeframe
                for tf_annotation in tf_view.get_annotations(AnnotationTypes.TimeFrame, frameType=FRAME_TYPE)
            ]
        # target_views = [bb_view for bb_view in views_with_bbox
        #                 if int(bb_view.properties["frame"]) in
        #                 itertools.chain([list(range(tf[0], tf[1]+1)) for tf in frame_number_ranges])
        #                 ]
        target_views = views_with_bbox #TODO: 4/29/21 kelleylynch incorporate filtering for frame type something like above comment
        mmif_obj = run_aligned_video(mmif_obj, new_view, target_views, box_type=BOX_TYPE, valid_frame_list=frame_number_ranges)
    else:
        target_views=views_with_bbox
        mmif_obj = run_aligned_image(mmif_obj, new_view, target_views, box_type=BOX_TYPE)
    return mmif_obj


def full_ocr(mmif_obj, new_view, **kwargs):
    tess_wrapper.BOX_THRESHOLD = kwargs["box_threshold"] if "box_threshold" in kwargs else 90
    tess_wrapper.PSM = kwargs["psm"] if "psm" in kwargs else None
    tess_wrapper.OEM = kwargs["oem"] if "oem" in kwargs else None
    tess_wrapper.CHAR_WHITELIST = kwargs["char_whitelist"] if "char_whitelist" in kwargs else None

    if mmif_obj.get_documents_by_type(DocumentTypes.VideoDocument):
        mmif_obj = run_video_tesseract(mmif_obj, new_view, **kwargs)
    else:
        mmif_obj = run_image_tesseract(mmif_obj, new_view)
    return mmif_obj
