import glob
import platform
import time

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
    WARMUP_FRAMES = 8
    READ_RETRY_DELAY_SECONDS = 0.05

    @staticmethod
    def _is_black_frame(cv2_module, frame, mean_thresh: int = 10, std_thresh: int = 5) -> bool:
        if frame is None:
            return True
        gray = cv2_module.cvtColor(frame, cv2_module.COLOR_BGR2GRAY)
        # Treat as black only when frame is both very dark and nearly flat.
        return gray.mean() < mean_thresh and gray.std() < std_thresh

    def _backends(self, cv2_module):
        """Return backends to try in priority order for this platform."""
        if platform.system() == "Windows":
            # MSMF is the stable index-based backend on modern Windows.
            # DSHOW and CAP_ANY are fallbacks.
            return [cv2_module.CAP_MSMF, cv2_module.CAP_DSHOW, cv2_module.CAP_ANY]
        return [cv2_module.CAP_V4L2, cv2_module.CAP_ANY]

    def _find_camera(self, cv2_module):
        """Return (index, backend) for the first working camera, or (None, None)."""
        candidates = []

        if platform.system() != "Windows":
            video_devices = sorted(glob.glob("/dev/video*"))
            for dev in video_devices:
                try:
                    candidates.append(int(dev.replace("/dev/video", "")))
                except ValueError:
                    continue

        if not candidates:
            candidates = list(range(self.MAX_DEVICE_INDEX + 1))

        self.log.info("WebCamera", f"Scanning camera indices: {candidates}")

        for backend in self._backends(cv2_module):
            for idx in candidates:
                try:
                    cap = cv2_module.VideoCapture(idx, backend)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue
                if not cap.isOpened():
                    cap.release()
                    continue
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    self.log.success("WebCamera", f"Found camera at index {idx} (backend={backend})")
                    return idx, backend

        self.log.error("WebCamera", "No working camera found")
        return None, None

    def capture(self) -> bool:
        import cv2  # pylint: disable=import-error

        device_index, backend = self._find_camera(cv2)
        if device_index is None:
            self.log.error("WebCamera", "Capture aborted because no camera was detected")
            return False

        backend_fallbacks = [backend] + [b for b in self._backends(cv2) if b != backend]

        for active_backend in backend_fallbacks:
            cap = cv2.VideoCapture(device_index, active_backend)
            if platform.system() != "Windows":
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)

            if not cap.isOpened():
                cap.release()
                self.log.warning(
                    "WebCamera", f"Could not open camera index {device_index} (backend={active_backend})"
                )
                continue

            start = time.time()
            frames_seen = 0
            invalid_reads = 0
            rejected_frames = 0

            while time.time() - start < self.MAX_WAIT_SECONDS:
                ret, frame = cap.read()
                if not ret or frame is None:
                    invalid_reads += 1
                    time.sleep(self.READ_RETRY_DELAY_SECONDS)
                    continue

                frames_seen += 1
                if frames_seen <= self.WARMUP_FRAMES:
                    time.sleep(self.READ_RETRY_DELAY_SECONDS)
                    continue

                if self._is_black_frame(cv2, frame):
                    rejected_frames += 1
                    time.sleep(self.READ_RETRY_DELAY_SECONDS)
                    continue

                cv2.imwrite(self.image_path, frame)
                cap.release()
                self.log.success(
                    "WebCamera",
                    f"Captured frame from index {device_index} (backend={active_backend}, warmup={self.WARMUP_FRAMES})",
                )
                return True

            cap.release()
            self.log.warning(
                "WebCamera",
                (
                    f"No valid frame from index {device_index} (backend={active_backend}) "
                    f"within {self.MAX_WAIT_SECONDS}s; "
                    f"invalid_reads={invalid_reads}, rejected_frames={rejected_frames}"
                ),
            )

        self.log.error(
            "WebCamera", f"Could not capture a valid frame before timeout (index={device_index})"
        )
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
    logger.info("Camera", "Using real webcam (OpenCV)")
    return RealWebCamera(image_path=image_path, logger=logger)
