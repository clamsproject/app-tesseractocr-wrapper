from typing import Tuple

from mmif import Mmif, Document, View, DocumentTypes, AnnotationTypes
from lapps.discriminators import Uri
from mmif.utils import video_document_helper as vdh
import numpy as np
import pytesseract
from collections import defaultdict

###################### GET_COORDS ##########################
def get_coords(left, top, width, height):  # I believe these are absolute coordinates but we should perhaps confirm
    return (left, top), (left + width, top + height)

def combine_coords(coord_list):
    smallest_left = min(t[0] for t in coord_list)
    smallest_top = min(t[1] for t in coord_list)
    largest_width = max(t[2]+t[0] for t in coord_list)
    largest_height = max(t[3]+t[1] for t in coord_list)
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
        # print(f"curr block: {result['block_num'][line_idx]}, last block: {result['block_num'][line_idx - 1]}")
        if ((line_idx > 0 and result['block_num'][line_idx] > result['block_num'][line_idx - 1]) or
                (line_idx > 0 and result['line_num'][line_idx] > result['line_num'][line_idx - 1])):
            sent_coords.append(combine_coords(curr_line_list))
            # print(f"curr line list: {curr_line_list}")
            curr_line_list = []
        # for each line, appends the tuples of the coordinates
        curr_line_list.append((result['left'][line_idx], result['top'][line_idx],
                                   result['width'][line_idx], result['height'][line_idx]))
        if line_idx == len(result['line_num']) - 1:
            sent_coords.append(combine_coords(curr_line_list))
    # print(f"sent tuples: {sent_tuples}")

    return token_coords, para_coords, sent_coords

# I also need something to build dicts of blocks
def build_dict(block_num, aligned_list):
    block_dict = defaultdict(list)
    for block_num, aligned_list in zip(block_num, aligned_list):
        block_dict[block_num].append(aligned_list)
    return block_dict

###################### PROCESS_TIME_ANNOTATION ##########################
def create_bbox(new_view: View,
                coordinates,
                timepoint_ann, text_ann):

    bbox_ann = new_view.new_annotation(AnnotationTypes.BoundingBox, coordinates=coordinates, label="text")
    for source_ann in [timepoint_ann, text_ann]:
        if source_ann.parent != new_view.id:
            source_id = source_ann.long_id
        else:
            source_id = source_ann.id
        new_view.new_annotation(AnnotationTypes.Alignment, source=source_id, target=bbox_ann.id)

###################### PROCESS_TIME_ANNOTATION ##########################

def process_time_annotation(mmif: Mmif, representative, new_view: View, video_doc: Document):
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
    h, w = image.shape[:2]
    result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    # assume only one page, as we are passing one image at a time
    text_content = pytesseract.image_to_string(image)
    # example render output: 'University of\nNorth Carolina\nTE - E V.. o oN\nUNC Bicentennial\nReel #1 -\nSync begins\n1:57:00\ninto Reel #1\nReellength: 2:00:00\nShow length: 2:27.27 STEREO'

    if not text_content:
        return timestamp, None
    text_document: Document = new_view.new_textdocument(text_content)
    td_id = text_document.id
    if representative.parent != new_view.id:
        source_id = representative.long_id
    else:
        source_id = representative.id

    new_view.new_annotation(AnnotationTypes.Alignment, source=source_id, target=td_id)

    text_block_dict = build_dict(result['block_num'], result['text'])
    line_nums = []
    for i in range(len(result['block_num'])):
        line_nums.append(result['line_num'][i] + (result['block_num'][i] * 10))  # change this to 100 later, what if there are more than 10 lines?
    text_line_dict = build_dict(line_nums, result['text'])

    token_coords, para_coords, sent_coords = get_all_coords(result)

    print(text_block_dict)
    print(result)
    print()

    end_index = 0
    for block in text_block_dict:
        print(f"block i: {text_block_dict[block]}")
        print(f"block: {block}")
        para_ann = new_view.new_annotation(Uri.PARAGRAPH, document=td_id, text=text_block_dict[block])
        create_bbox(new_view, para_coords.pop(0), representative, para_ann)
        target_sents = []

        for line in text_line_dict:
            if int(line/10) == block:
        # for line_i in range(len(result['line_num'])):
        #     if ((result['block_num'][line_i] == block_i and result['block_num'][line_i] > result['block_num'][line_i - 1]) or
        #             (result['block_num'][line_i] == block_i and line_i == 0)):
        #         print(f"line i: {result['text'][line_i]}")
                # the issue is this result['text'][number] isn't wokring
                print(f"line i: {text_line_dict[line]}")
                print(f"line num: {line}")
                line_ann = new_view.new_annotation(Uri.SENTENCE, document=td_id, text=text_line_dict[line])
                target_sents.append(line_ann.id)
                create_bbox(new_view, sent_coords.pop(0), representative, line_ann)
                target_tokens = []

                for word in text_line_dict[line]:
                # for word in range(len(result['text'])):
                #     if ((result['line_num'][word_i] == line_i and result['line_num'][word_i] > result['line_num'][word_i - 1]) or
                #             (result['line_num'][word_i] == line_i and word_i == 0)):
                        if word == '':
                            print("empty word")
                        else:
                            print(f"word i: {word}")
                        start_index = text_content.find(word, end_index)
                        end_index = start_index + len(word)

                        word_ann = new_view.new_annotation(Uri.TOKEN, document=td_id,
                                                            start=start_index,
                                                            end=end_index,
                                                            text=word,
                                                            word=word)
                        target_tokens.append(word_ann.id)
                        create_bbox(new_view, token_coords.pop(0), representative, word_ann)
                line_ann.add_property("targets", target_tokens)
        para_ann.add_property("targets", target_sents)

    return timestamp, text_content



#################### ANNOTATION TESTS #################

with open("cpb-aacip-06c4069f088.fixed.mmif", 'r') as f:
    content = f.read()
    mmif = Mmif(content)

# now that we have the mmif, we can run experiments on it
video_doc: Document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
input_view: View = mmif.get_views_for_document(video_doc.properties.id)[-1]

new_view: View = mmif.new_view()
# sign_view(new_view, parameters)
new_view.new_contain(DocumentTypes.TextDocument)
new_view.new_contain(AnnotationTypes.BoundingBox)
new_view.new_contain(AnnotationTypes.Alignment)
new_view.new_contain(Uri.PARAGRAPH)
new_view.new_contain(Uri.SENTENCE)
new_view.new_contain(Uri.TOKEN)

futures = []
for timeframe in input_view.get_annotations(AnnotationTypes.TimeFrame):
    # print(timeframe)
    if 'label' in timeframe:
        print(f'Found a time frame "{timeframe.id}" of label: "{timeframe.get("label")}"')
    else:
        print(f'Found a time frame "{timeframe.id}" without label')
    # basically if there is a specific timeframe we want to look at, we can call that label to be processed as well
    # if parameters.get("tfLabel") and \
    #         'label' in timeframe and timeframe.get("label") not in parameters.get("tfLabel"):
    #     continue
    # else:
    #     self.logger.debug(f'Processing time frame "{timeframe.id}"')

    for rep_id in timeframe.get("representatives"):
        if Mmif.id_delimiter not in rep_id:
            rep_id = f'{input_view.id}{Mmif.id_delimiter}{rep_id}'
        representative = mmif[rep_id]
        futures.append(process_time_annotation(mmif, representative, new_view, video_doc))
    if len(futures) == 0:
        # meaning "representatives" was not present, so alternatively, just process the middle frame
        futures.append(process_time_annotation(mmif, timeframe, new_view, video_doc))
        pass


# note that in the output it has several outputs because in addition to the slates there are bars and chyrons in the test video
for future in futures:
    print(future)

print()
# print(mmif)


# example outputs:
# result = {'level': [1, 2, 3, 4, 5, 2, 3, 4, 5, 4, 5, 5, 5, 4, 5, 5, 4, 5, 4, 5, 5, 5, 2, 3, 4, 5, 5], 'page_num': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 'block_num': [0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3], 'par_num': [0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1], 'line_num': [0, 0, 0, 1, 1, 0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5, 5, 0, 0, 1, 1, 1], 'word_num': [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 2, 3, 0, 1, 2, 0, 1, 0, 1, 2, 3, 0, 0, 0, 1, 2], 'left': [0, 0, 0, 0, 0, 84, 84, 84, 84, 106, 106, 162, 203, 108, 108, 184, 107, 107, 199, 199, 294, 350, 106, 106, 106, 106, 220], 'top': [0, 0, 0, 0, 0, 79, 79, 79, 108, 118, 118, 118, 118, 156, 156, 156, 198, 198, 235, 235, 235, 231, 281, 281, 281, 281, 281], 'width': [480, 480, 480, 480, 480, 281, 281, 26, 5, 148, 48, 31, 51, 156, 58, 80, 194, 110, 166, 85, 71, 18, 204, 204, 204, 99, 90], 'height': [360, 150, 150, 150, 150, 182, 182, 31, 2, 28, 28, 26, 24, 23, 23, 23, 23, 23, 26, 26, 22, 34, 24, 24, 24, 24, 23], 'conf': [-1, -1, -1, -1, 95, -1, -1, -1, 2, -1, 94, 96, 96, -1, 96, 96, -1, 0, -1, 22, 24, 31, -1, -1, -1, 96, 96], 'text': ['', '', '', '', ' ', '', '', '', 'Fr', '', 'July', '25,', '2008', '', 'Host:', 'Barnes', '', 'GSA', '', 'OTE', 'CMA', 'Cy', '', '', '', 'Director:', 'Worden']}
# result = {'level': [1, 2, 3, 4, 5], 'page_num': [1, 1, 1, 1, 1], 'block_num': [0, 1, 1, 1, 1], 'par_num': [0, 0, 1, 1, 1], 'line_num': [0, 0, 0, 1, 1], 'word_num': [0, 0, 0, 0, 1], 'left': [0, 0, 0, 0, 0], 'top': [0, 0, 0, 0, 0], 'width': [480, 278, 278, 278, 278], 'height': [360, 360, 360, 360, 360], 'conf': [-1, -1, -1, -1, 95], 'text': ['', '', '', '', '']}
