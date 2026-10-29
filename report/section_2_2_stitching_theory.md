
# 2.2. Image Stitching Theory

## 2.2.1. Overview

Image stitching combines multiple overlapping images into a single panoramic
image. The images should contain sufficient common visual information to
estimate their relative geometric transformations.

The pipeline consists of feature detection and description, feature matching,
homography estimation, image warping, and blending.

## 2.2.2. Feature Detection and Description

SIFT, SURF, and ORB are feature detection and description methods.

SIFT detects distinctive keypoints across image scales and generates
descriptors that are comparatively robust to scale and rotation changes.
SURF follows a similar objective while using approximations designed to
improve computational efficiency. ORB combines FAST keypoint detection
with oriented BRIEF binary descriptors.

SIFT and SURF descriptors are commonly matched using Euclidean distance,
whereas ORB descriptors use Hamming distance.

## 2.2.3. Feature Matching

For each pair of consecutive images, feature descriptors are matched using
a brute-force matcher. The k-nearest-neighbors procedure finds the two
nearest candidates for each descriptor.

Lowe's ratio test retains a match when

d1 < r * d2,

where d1 and d2 are the distances to the nearest and second-nearest
candidates, respectively, and r is a threshold.

This test helps reject ambiguous matches, although incorrect matches
may remain.

## 2.2.4. Homography Estimation

For two views of a planar scene, or views related by pure camera rotation,
a homography can model the projective transformation between corresponding
image points:

x' ~ Hx,

where x and x' are homogeneous image coordinates and H is a 3 x 3
homography matrix defined up to scale.

At least four non-collinear point correspondences are required to estimate
a homography. RANSAC estimates the transformation robustly by identifying
a consensus set of inlier correspondences while rejecting outliers.

The reprojection error measures the distance between an observed
corresponding point and its projected location under the estimated
homography.

## 2.2.5. Image Warping and Blending

After estimating pairwise homographies, the images are transformed into
a common coordinate system. Their transformed corner coordinates determine
the panorama canvas.

The warped images are then combined. This implementation averages pixel
values in overlapping regions using validity masks. This simple blending
strategy is reproducible but may produce ghosting or visible seams when
images contain moving objects, exposure differences, or inaccurate
alignment.

## 2.2.6. Evaluation Metrics

The implementation records the number of detected keypoints, tentative
matches, RANSAC inliers, inlier ratio, reprojection error, and processing
time.

These measurements provide complementary information. A large number of
keypoints does not necessarily imply accurate stitching; geometric
consistency and the quality of the final panorama must also be considered.
