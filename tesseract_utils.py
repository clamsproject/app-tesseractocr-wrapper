from lapps.discriminators import Uri
from mmif import Mmif, View, Document, AnnotationTypes
from mmif.utils import video_document_helper as vdh

from typing import Tuple, DefaultDict
from collections import defaultdict
import numpy as np
import pytesseract

def build_dict(block_num, aligned_list):
    """Creates a dictionary of blocks with the block number as the key and a list of aligned coordinates as the value."""
    block_dict = defaultdict(list)
    for block_num, aligned_list in zip(block_num, aligned_list):
        block_dict[block_num].append(aligned_list)
    return block_dict

def get_coords(left, top, width, height):
    """Organizing the coordinates into tuples"""
    return (left, top), (left + width, top + height)

def combine_coords(coord_list):
    """Given a list of tuples, return the smallest left, smallest top, largest width, largest height tuple."""
    smallest_left = min(t[0] for t in coord_list)
    smallest_top = min(t[1] for t in coord_list)
    largest_width = max(t[2] + t[0] for t in coord_list)
    largest_height = max(t[3] + t[1] for t in coord_list)
    return (smallest_left, smallest_top), (largest_width - smallest_left, largest_height - smallest_top)

def get_all_coords(result: dict) -> Tuple[list, list, list]:
    """Get the coordinates of all the words, lines, and paragraphs in the image."""
    # word coordinates
    token_coords = []
    for left, top, width, height in zip(result['left'], result['top'], result['width'], result['height']):
        token_coords.append(get_coords(left, top, width, height))

    # paragraph coordinates, paragraphs come from blocks
    para_coords = []
    left_block_dict = build_dict(result['block_num'], result['left'])
    top_block_dict = build_dict(result['block_num'], result['top'])
    width_block_dict = build_dict(result['block_num'], result['width'])
    height_block_dict = build_dict(result['block_num'], result['height'])
    for block in left_block_dict:
        para_coords.append(get_coords(min(left_block_dict[block]), min(top_block_dict[block]),
                                      max(width_block_dict[block]) - min(left_block_dict[block]),
                                      max(height_block_dict[block]) - min(top_block_dict[block])))

    # sentence coordinates, sentences come from the line annotations
    sent_coords = []
    curr_line_list = []
    for line_idx in range(len(result['line_num'])):
        if ((line_idx > 0 and result['block_num'][line_idx] > result['block_num'][line_idx - 1]) or
                (line_idx > 0 and result['line_num'][line_idx] > result['line_num'][line_idx - 1])):
            sent_coords.append(combine_coords(curr_line_list))
            curr_line_list = []
        # for each line, appends the tuples of the coordinates
        curr_line_list.append((result['left'][line_idx], result['top'][line_idx],
                               result['width'][line_idx], result['height'][line_idx]))
        if line_idx == len(result['line_num']) - 1:
            sent_coords.append(combine_coords(curr_line_list))

    return token_coords, para_coords, sent_coords

def create_bbox(new_view: View,
                coordinates,
                timepoint_ann, text_ann):
    """Creates a bounding box annotation and links it to the timepoint and text annotations."""
    bbox_ann = new_view.new_annotation(AnnotationTypes.BoundingBox, coordinates=coordinates, label="text")
    for source_ann in [timepoint_ann, text_ann]:
        if source_ann.parent != new_view.id:
            source_id = source_ann.long_id
        else:
            source_id = source_ann.id
        new_view.new_annotation(AnnotationTypes.Alignment, source=source_id, target=bbox_ann.id)

def create_line_dict(result_dict: dict) -> DefaultDict[int, list]:
    """Creates a dictionary of lines with the line number as the key and a list of words as the value."""
    line_nums = []
    for i in range(len(result_dict['block_num'])):
        line_nums.append(result_dict['line_num'][i] + (
                    result_dict['block_num'][i] * 100))  # multiplied by 100 so that there can be up to 100 sentences in a paragraph
    text_line_dict = build_dict(line_nums, result_dict['text'])
    return text_line_dict

def process_time_annotation(mmif: Mmif, representative, new_view: View, video_doc: Document):
    """Processes a time annotation, getting all the views for paragraphs, sentences, and tokens, as well as the bounding boxes for each of these"""
    # get the initial data structures from pytesseract
    if representative.at_type == AnnotationTypes.TimePoint:
        rep_frame_index = vdh.convert(representative.get("timePoint"),
                                      representative.get("timeUnit"), "frame",
                                      video_doc.get("fps"))
        image: np.ndarray = vdh.extract_frames_as_images(video_doc, [rep_frame_index], as_PIL=False)[0]
        timestamp = vdh.convert(representative.get("timePoint"),
                                representative.get("timeUnit"), "ms", video_doc.get("fps"))
    elif representative.at_type == AnnotationTypes.TimeFrame:
        image: np.ndarray = vdh.extract_mid_frame(mmif, representative, as_PIL=False)
        timestamp = vdh.convert(vdh.get_mid_framenum(mmif, representative),
                                'f', 'ms', video_doc.get("fps"))
    else:
        print(f"Representative annotation type {representative.at_type} is not supported.")
        return -1, None
    result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text_content = pytesseract.image_to_string(image) # assume only one page, as we are passing one image at a time
    # example render output: 'University of\nNorth Carolina\nTE - E V.. o oN\nUNC Bicentennial\nReel #1 -\nSync begins\n1:57:00\ninto Reel #1\nReellength: 2:00:00\nShow length: 2:27.27 STEREO'

    # initialize the new text document
    if not text_content:
        return timestamp, None
    text_document: Document = new_view.new_textdocument(text_content)
    td_id = text_document.id
    if representative.parent != new_view.id:
        source_id = representative.long_id
    else:
        source_id = representative.id
    new_view.new_annotation(AnnotationTypes.Alignment, source=source_id, target=td_id)

    # initializing variables and datastructures for extracting data
    text_block_dict = build_dict(result['block_num'], result['text'])
    text_line_dict = create_line_dict(result)
    print(f"here are the lines: {text_line_dict}")
    token_coords, para_coords, sent_coords = get_all_coords(result)
    end_index = 0

    # looping through each block in the results data to get the paragraphs, then finding the sentences and tokens within each paragraph
    for block in text_block_dict:
        para_ann = new_view.new_annotation(Uri.PARAGRAPH, document=td_id, text=text_block_dict[block])
        create_bbox(new_view, para_coords.pop(0), representative, para_ann)
        target_sents = []

        for line in text_line_dict:
            if int(line / 100) == block:
                line_ann = new_view.new_annotation(Uri.SENTENCE, document=td_id, text=text_line_dict[line])
                target_sents.append(line_ann.id)
                create_bbox(new_view, sent_coords.pop(0), representative, line_ann)
                target_tokens = []

                for word in text_line_dict[line]:
                        start_index = text_content.find(word, end_index)  # note that this currently includes \n as part of the indices of the text_content
                        end_index = start_index + len(word)

                        word_ann = new_view.new_annotation(Uri.TOKEN, document=td_id,
                                                           start=start_index,
                                                           end=end_index,
                                                           text=word)
                        target_tokens.append(word_ann.id)
                        create_bbox(new_view, token_coords.pop(0), representative, word_ann)
                line_ann.add_property("targets", target_tokens)
        para_ann.add_property("targets", target_sents)

    return timestamp, text_content