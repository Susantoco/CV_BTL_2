import argparse

import cv2
import numpy as np


class PolygonMaskTool:
    def __init__(self, image):
        self.image = image
        self.points = []
        self.mask = np.zeros(image.shape[:2], dtype=np.uint8)

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and self.points:
            self.points.pop()

    def _render(self):
        canvas = self.image.copy()
        if self.mask.any():
            overlay = canvas.copy()
            overlay[self.mask > 0] = (0, 255, 0)
            canvas = cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0)
        for i, p in enumerate(self.points):
            cv2.circle(canvas, p, 3, (0, 0, 255), -1)
            if i > 0:
                cv2.line(canvas, self.points[i - 1], p, (0, 0, 255), 1)
        if len(self.points) > 2:
            cv2.line(canvas, self.points[-1], self.points[0], (0, 0, 255), 1, cv2.LINE_AA)
        return canvas

    def run(self):
        win = "Mask tool (polygon) - c: close, r: reset, s: save, q: quit"
        cv2.namedWindow(win)
        cv2.setMouseCallback(win, self._on_mouse)
        while True:
            cv2.imshow(win, self._render())
            key = cv2.waitKey(20) & 0xFF
            if key == ord('c') and len(self.points) > 2:
                self.mask[:] = 0
                cv2.fillPoly(self.mask, [np.array(self.points, dtype=np.int32)], 255)
            elif key == ord('r'):
                self.points = []
                self.mask[:] = 0
            elif key == ord('s'):
                cv2.destroyWindow(win)
                return self.mask
            elif key == ord('q') or key == 27:
                cv2.destroyWindow(win)
                return None


class BrushMaskTool:
    def __init__(self, image, brush_size=15):
        self.image = image
        self.mask = np.zeros(image.shape[:2], dtype=np.uint8)
        self.brush_size = brush_size
        self.drawing = False

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
        if self.drawing and event in (cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN):
            cv2.circle(self.mask, (x, y), self.brush_size, 255, -1)

    def _render(self):
        overlay = self.image.copy()
        overlay[self.mask > 0] = (0, 255, 0)
        return cv2.addWeighted(overlay, 0.35, self.image, 0.65, 0)

    def run(self):
        win = "Mask tool (brush) - r: reset, s: save, q: quit"
        cv2.namedWindow(win)
        cv2.setMouseCallback(win, self._on_mouse)
        while True:
            cv2.imshow(win, self._render())
            key = cv2.waitKey(20) & 0xFF
            if key == ord('r'):
                self.mask[:] = 0
            elif key == ord('s'):
                cv2.destroyWindow(win)
                return self.mask
            elif key == ord('q') or key == 27:
                cv2.destroyWindow(win)
                return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="The path to the source image (.png) to be used for mask creation")
    parser.add_argument("--out", required=True, help="The path to the output mask file (.png) to be saved")
    parser.add_argument("--mode", choices=["polygon", "brush"], default="polygon")
    parser.add_argument("--brush-size", type=int, default=15)
    args = parser.parse_args()

    image = cv2.imread(args.source, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {args.source}")

    tool = (PolygonMaskTool(image) if args.mode == "polygon"
            else BrushMaskTool(image, brush_size=args.brush_size))
    mask = tool.run()
    if mask is None:
        print("Exit without saving mask.")
        return
    cv2.imwrite(args.out, mask)
    print(f"Data saved to: {args.out}")


if __name__ == "__main__":
    main()
