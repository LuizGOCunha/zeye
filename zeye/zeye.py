import cv2
import numpy as np
import pyautogui
import pytesseract

class Zeye:
    click_history = []

    def click_by_image(self, image_path:str, match_confidence=0.8):
        # Step 1: Take a screenshot
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

        # Step 2: Load template
        template = cv2.imread(image_path, cv2.IMREAD_COLOR)
        template_h, template_w = template.shape[:2]

        # Step 3: Template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

        # Step 4: Find best match location
        _, max_val, _, max_loc = cv2.minMaxLoc(result) 

        if max_val >= match_confidence:
            # Calculate center of the found region
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2

            print(f"Found target with confidence {max_val:.2f}")
            print(f"Center coordinates: ({center_x}, {center_y})")

            # Step 5 (optional): Move or click
            pyautogui.moveTo(center_x, center_y)
            pyautogui.click()

            # Step 6 (optional): Visual feedback
            cv2.rectangle(screen, max_loc, 
                        (max_loc[0] + template_w, max_loc[1] + template_h),
                        (0, 255, 0), 2)
            cv2.imshow("Match", screen)
            self.click_history.append(screen)
        else:
            print("Target not found. Try lowering the threshold or checking the image.")

    def click_by_string(self, target_string):
        # Step 1: Take a screenshot
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

        # Step 2: Use pytesseract to get data with bounding boxes
        data = pytesseract.image_to_data(screen, output_type=pytesseract.Output.DICT)

        # Step 3: Iterate through words to find the phrase
        words = data["text"]
        found = False
        i = 0
        while i < len(words):
            # Build a candidate phrase from consecutive words
            candidate_words = words[i:i + len(target_string.split())]
            candidate_phrase = " ".join(candidate_words)
            
            if candidate_phrase == target_string:
                # Get bounding box of the first and last word
                x1, y1 = data["left"][i], data["top"][i]
                x2 = data["left"][i + len(candidate_words) - 1] + data["width"][i + len(candidate_words) - 1]
                y2 = data["top"][i + len(candidate_words) - 1] + data["height"][i + len(candidate_words) - 1]

                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                print(f"Found phrase at center: ({center_x}, {center_y})")
                found = True

                # Optional: highlight on screen
                cv2.rectangle(screen, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.imshow("Detected Phrase", screen)
                self.click_history.append(screen)


                pyautogui.moveTo(center_x, center_y)
                pyautogui.click()
                break

            i += 1

        if not found:
            print(f"Phrase '{target_string}' not found on screen.")

    def dump_click_history(directory: str = ""):
        for index in range(len(z.click_history)):
            cv2.imwrite(f"click_{index+1}.jpg", z.click_history[index])
    

z = Zeye()
z.click_by_image("C:\\Users\\Luiz\\Pictures\\pikito.png")
z.click_by_string("CLICK ME")


z.click_history