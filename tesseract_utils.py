import collections

import pytesseract

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
