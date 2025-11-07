import cv2
import numpy as np
import pyautogui
import pytesseract

import os
from time import time

class Zeye:
    """A lightweight library that allows an automation to see elements in the desktop and interact with them using CV and OCR."""
    click_history = []

    def _screen_grab(self) -> np.ndarray:
        """Takes a screenshot of the desktop, turns it into a np array and corrects it's colors for use in cv2.

        Returns:
            np.ndarray: image array of desktop.
        """
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    def click_by_image(self, image_path: str, match_confidence: float = 0.8, timeout: int = 5) -> bool:
        """Waiting for, finding and clicking an image when it appears in the desktop.

        Args:
            image_path (str): path for the image that is being searched
            match_confidence (float, optional): Measure how similar it needs to be to searched image. Defaults to 0.8.
            timeout (int, optional): time we wait for the image to show up. Defaults to 5.

        Returns:
            bool: If the operation was successful or not.
        """
        screen = self._screen_grab()

        timeout_epoch = timeout + time()
        while time() < timeout_epoch:
            found, rectangle_coord = self.find_image(image_path, screen, match_confidence)
            if found:
                center_x, center_y = self._get_center(rectangle_coord)

                self._click_at_coordenates(center_x, center_y)

                self._add_to_history(rectangle_coord, screen)
                return True
        return False

    def _get_center(self, rectangle_coord: tuple[int, int, int, int]) -> tuple[int, int]:
        """Get x and y axis for a point in the center of a triangle

        Args:
            rectangle_coord (tuple[int, int, int, int]): the four values that represent a rectangle coordinate.

        Returns:
            tuple[int, int]: x and y coordinates in the center of a triangle.
        """
        x1, y1, x2, y2 = rectangle_coord
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return center_x, center_y

    def _highcontrast_img(self, img) -> np.ndarray:
        """Increase the contrast of an image array.

        Args:
            img (np.ndarray): Image array to increase contrast.

        Returns:
            np.ndarray: high contrasted image.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, high_contrast = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return high_contrast

    def _invert_img(self, img: np.ndarray) -> np.ndarray:
        """Inverts the color of a given image array.

        Args:
            img (np.ndarray): image array to have its colors inverted.

        Returns:
            np.ndarray: inverted image array.
        """
        return cv2.bitwise_not(img)

    def find_image(self, image_path: str, screen: np.ndarray, match_confidence: float) -> tuple[bool, tuple]:
        template = cv2.imread(image_path, cv2.IMREAD_COLOR)
        template_h, template_w = template.shape[:2]

        # Step 3: Template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

        # Step 4: Find best match location
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= match_confidence:
            # Calculate center of the found region
            x1, y1 = max_loc
            x2 = max_loc[0] + template_w
            y2 = max_loc[1] + template_h

            return True, (x1, y1, x2, y2)

        return False, ()

    def find_text(self, screen: np.ndarray, target_string: str) -> tuple[bool, tuple]:
        """Finds the given text inside of a given image array.

        Args:
            screen (np.ndarray): screenshot of desktop with any given modifications.
            target_string (str): string of the text you want to look for.

        Returns:
            tuple[bool, tuple]: boolean is related to success, second contains the coordenates of text found (x1, y1, x2, y2)
        """
        data = pytesseract.image_to_data(screen, output_type=pytesseract.Output.DICT)

        # Step 3: Iterate through words to find the phrase
        words = data["text"]
        i = 0
        while i < len(words):
            # Build a candidate phrase from consecutive words
            candidate_words = words[i : i + len(target_string.split())]
            candidate_phrase = " ".join(candidate_words)

            if candidate_phrase == target_string:
                # Get bounding box of the first and last word
                x1, y1 = data["left"][i], data["top"][i]
                x2 = data["left"][i + len(candidate_words) - 1] + data["width"][i + len(candidate_words) - 1]
                y2 = data["top"][i + len(candidate_words) - 1] + data["height"][i + len(candidate_words) - 1]
                return True, (x1, y1, x2, y2)

            i += 1

        return False, ()

    def _click_at_coordenates(self, x: int, y: int) -> None:
        """Click the point given from the coordenates.

        Args:
            x (int): x axis coordenate.
            y (int): y axis coordenate.
        """
        pyautogui.moveTo(x, y)
        pyautogui.click()

    def _add_to_history(self, rectangle_coord: tuple[int, int, int, int], screen: np.ndarray) -> None:
        """Adds an image of where in the desktop did we click to the click history

        Args:
            rectangle_coord (tuple[int, int, int, int]): coordenates of rectangle (x1, y1, x2, y2)
            screen (np.ndarray): array picture of the entire desktop
        """
        x1, y1, x2, y2 = rectangle_coord
        cv2.rectangle(screen, (x1, y1), (x2, y2), (0, 255, 0), 2)
        self.click_history.append(screen)

    def click_by_string(
        self, target_string, high_contrast: bool = False, invert: bool = False, timeout: int = 5
    ) -> bool:
        """Waits, finds and clicks a given string within the desktop.

        Args:
            target_string (_type_): String to be found.
            high_contrast (bool, optional): If the desktop image should be converted to high contrast. Defaults to False.
            invert (bool, optional): If the desktop image should be inverted. Defaults to False.
            timeout (int, optional): How many seconds should we wait for this string to show up. Defaults to 5.

        Returns:
            bool: If the operation was successful or not.
        """
        original_screen = self._screen_grab()
        screen = original_screen

        if high_contrast:
            screen = self._highcontrast_img(screen)
        if invert:
            screen = self._invert_img(screen)

        timeout_epoch = time() + timeout
        while time() < timeout_epoch:
            found, rectangle_coord = self.find_text(screen, target_string)
            if found:
                x1, y1, x2, y2 = rectangle_coord
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                self._click_at_coordenates(center_x, center_y)

                self._add_to_history(rectangle_coord, original_screen)
                return True
        return False

    def dump_click_history(self, directory: str = "") -> None:
        """Dumps click history files in a given directory and enumeartes them in order of click.

        Args:
            directory (str, optional): directory where the files will be dumped. Defaults to "".
        """
        for index in range(len(self.click_history)):
            cv2.imwrite(os.path.join(directory, f"click_{index+1}.jpg"), self.click_history[index])
