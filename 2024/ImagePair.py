from Datatypes import *
from Frame import Frame
import numpy as np
import cv2

class ImagePair():
    """
    Class for working with image pairs.
    """
    def __init__(self, frame1: Frame, frame2: Frame, matcher, camera_matrix):
        self.frame1 = frame1
        self.frame2 = frame2
        self.matcher = matcher
        self.camera_matrix = camera_matrix


    def match_features(self):
        temp = self.matcher.match(
                self.frame1.descriptors, 
                self.frame2.descriptors)
        # Make a list with the following values
        # - feature 1 id
        # - feature 2 id
        # - image coordinate 1
        # - image coordinate 2
        # - match distance
        self.raw_matches: list[Match] = [
                Match(self.frame1.features[match.queryIdx].feature_id, 
                    self.frame2.features[match.trainIdx].feature_id,
                    self.frame1.features[match.queryIdx].keypoint.pt, 
                    self.frame2.features[match.trainIdx].keypoint.pt, 
                    self.frame1.features[match.queryIdx].descriptor, 
                    self.frame2.features[match.trainIdx].descriptor,
                    match.distance, np.random.random((3))) 
                for idx, match
                in enumerate(temp)]


        # Perform a very crude filtering of the matches
        self.filtered_matches: list[Match] = [match
                for match
                in self.raw_matches
                if match.distance < 1130]


    def visualize_matches(self, matches):
        h, w, _ = self.frame1.image.shape
        # Place the images next to each other.
        vis = np.concatenate((self.frame1.image, self.frame2.image), axis=1)

        # Draw the matches
        for match in matches:
            start_coord = (int(match.keypoint1[0]), int(match.keypoint1[1]))
            end_coord = (int(match.keypoint2[0] + w), int(match.keypoint2[1]))
            thickness = 1
            color = list(match.color * 256)
            vis = cv2.line(vis, start_coord, end_coord, color, thickness)

        return vis


    def determine_essential_matrix(self, matches):
        points_in_frame_1, points_in_frame_2 = self.get_image_points(matches)

        confidence = 0.99
        ransacReprojecThreshold = 1
        self.essential_matrix, mask = cv2.findEssentialMat(
                points_in_frame_1,
                points_in_frame_2, 
                self.camera_matrix, 
                cv2.FM_RANSAC, 
                confidence,
                ransacReprojecThreshold)
        print("Essential matrix")
        print(self.essential_matrix)
        '''
        # Assuming E is the essential matrix and K is the intrinsic matrix
        F = np.linalg.inv(self.camera_matrix).T @ self.essential_matrix @ np.linalg.inv(self.camera_matrix)

        # For each point match
        distances = []
        for match in matches:
            pt1 = np.array([*match.keypoint1, 1.0])  # point in image 1
            pt2 = np.array([*match.keypoint2, 1.0])  # point in image 2

            # l2 is the epipolar line in image 2 corresponding to pt1
            l2 = F @ pt1
            a, b, c = l2
            d = abs(a * pt2[0] + b * pt2[1] + c) / np.sqrt(a**2 + b**2)
            distances.append(d)

        # Statistics
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        print(f"Mean epipolar distance: {mean_dist:.4f}")
        print(f"Std of epipolar distance: {std_dist:.4f}")
        '''

        inlier_matches = [match 
                for match, inlier in zip(matches, mask.ravel() == 1)
                if inlier]

        return inlier_matches


    def get_image_points(self, matches):
        points_in_frame_1 = np.array(
                [match.keypoint1 for match in matches], dtype=np.float64)
        points_in_frame_2 = np.array(
                [match.keypoint2 for match in matches], dtype=np.float64)
        return points_in_frame_1, points_in_frame_2


    def estimate_camera_movement(self, matches):
        points_in_frame_1, points_in_frame_2 = self.get_image_points(matches)

        retval, self.R, self.t, mask = cv2.recoverPose(
                self.essential_matrix, 
                points_in_frame_1, 
                points_in_frame_2, 
                self.camera_matrix)
        self.relative_pose = np.eye(4)
        self.relative_pose[:3, :3] = self.R
        self.relative_pose[:3, 3] = self.t.T[0]

        print("relative movement in image pair")
        print(self.relative_pose)


    def reconstruct_3d_points(self, matches, 
            first_projection_matrix = None, 
            second_projection_matrix = None):
        identify_transform = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
        estimated_transform = np.hstack((self.R.T, -self.R.T @ self.t))

        self.null_projection_matrix = self.camera_matrix @ identify_transform
        self.projection_matrix = self.camera_matrix @ estimated_transform

        if first_projection_matrix is not None:
            self.null_projection_matrix = self.camera_matrix @ first_projection_matrix
        if second_projection_matrix is not None:
            self.projection_matrix = self.camera_matrix @ second_projection_matrix

        points_in_frame_1, points_in_frame_2 = self.get_image_points(matches)

        self.points3d_reconstr = cv2.triangulatePoints(
                self.projection_matrix, 
                self.null_projection_matrix,
                points_in_frame_1.T, 
                points_in_frame_2.T) 

        # Convert back to unit value in the homogeneous part.
        self.points3d_reconstr /= self.points3d_reconstr[3, :]

        self.matches_with_3d_information = [
                Match3D(match.featureid1, match.featureid2, 
                    match.keypoint1, match.keypoint2, 
                    match.descriptor1, match.descriptor2, 
                    match.distance, match.color,
                    (self.points3d_reconstr[0, idx],
                        self.points3d_reconstr[1, idx],
                        self.points3d_reconstr[2, idx]))
                for idx, match 
                in enumerate(matches)]
        
        #print("Reconstructed points")
        #print(self.points3d_reconstr.transpose().shape)
        #print(self.points3d_reconstr.transpose())