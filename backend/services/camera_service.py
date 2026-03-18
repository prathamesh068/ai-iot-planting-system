import glob
import time
from typing import Optional

from backend.contracts import BaseCamera


class BaseCameraService(BaseCamera):
    def __init__(self, image_path: str, logger):
        self.image_path = image_path
        self.log = logger

    def capture(self) -> bool:
        raise NotImplementedError


class RealWebCamera(BaseCameraService):
    MAX_DEVICE_INDEX = 5
    MAX_WAIT_SECONDS = 10
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480

    @staticmethod
    def _is_black_frame(cv2_module, frame, mean_thresh: int = 10, std_thresh: int = 5) -> bool:
        if frame is None:
            return True
        gray = cv2_module.cvtColor(frame, cv2_module.COLOR_BGR2GRAY)
        return gray.mean() < mean_thresh or gray.std() < std_thresh

    def _find_camera_index(self, cv2_module) -> Optional[int]:
        candidates = []

        video_devices = sorted(glob.glob("/dev/video*"))
        for dev in video_devices:
            try:
                idx = int(dev.replace("/dev/video", ""))
                candidates.append(idx)
            except ValueError:
                continue

        if not candidates:
            candidates = list(range(self.MAX_DEVICE_INDEX + 1))

        self.log.info("WebCamera", f"Scanning camera indices: {candidates}")

        for idx in candidates:
            cap = cv2_module.VideoCapture(idx, cv2_module.CAP_V4L2)
            if not cap.isOpened():
                cap.release()
                continue

            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                self.log.success("WebCamera", f"Found camera at /dev/video{idx}")
                return idx

            self.log.warning("WebCamera", f"Camera index {idx} could not return frames")

        self.log.error("WebCamera", "No working camera found")
        return None

    def capture(self) -> bool:
        import cv2  # pylint: disable=import-error

        device_index = self._find_camera_index(cv2)
        if device_index is None:
            self.log.error("WebCamera", "Capture aborted because no camera was detected")
            return False

        cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)

        if not cap.isOpened():
            cap.release()
            self.log.error("WebCamera", f"Could not open camera index {device_index}")
            return False

        time.sleep(2)
        start = time.time()

        while time.time() - start < self.MAX_WAIT_SECONDS:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            if self._is_black_frame(cv2, frame):
                continue

            cv2.imwrite(self.image_path, frame)
            cap.release()
            return True

        cap.release()
        self.log.error("WebCamera", "Could not capture a valid frame before timeout")
        return False


class MockCameraService(BaseCameraService):
    def capture(self) -> bool:
        # We write placeholder bytes so downstream code has a file path to work with.
        with open(self.image_path, "wb") as image_file:
            image_file.write(b"mock-image")
        self.log.info("MockCamera", f"Created mock image: {self.image_path}")
        return True


def create_camera_service(is_mock: bool, image_path: str, logger) -> BaseCameraService:
    if is_mock:
        return MockCameraService(image_path=image_path, logger=logger)
    return RealWebCamera(image_path=image_path, logger=logger)
