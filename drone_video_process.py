import cv2
import os

def save_frames(video_path, output_dir, skip_frames=1200, save_every=25):
    """
    Processes a video, skips the first `skip_frames`, and saves every `save_every`th frame to disk.

    Args:
        video_path (str): Path to the input video file.
        output_dir (str): Directory where frames will be saved.
        skip_frames (int): Number of frames to skip at the start of the video.
        save_every (int): Save every nth frame after skipping.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return

    frame_count = 0
    saved_frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Exit loop if no more frames

        # Skip the first `skip_frames` frames
        if frame_count < skip_frames:
            frame_count += 1
            continue

        # Save every `save_every`th frame
        if (frame_count - skip_frames) % save_every == 0:
            print(f"Processing frame {frame_count}...")
            frame_filename = f"frame_{saved_frame_count:05d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            saved_frame_count += 1

        frame_count += 1

    cap.release()
    print(f"Processing complete. Saved {saved_frame_count} frames to {output_dir}.")

# Example usage
if __name__ == "__main__":
    video_path = "DJI_0199.MOV"  # Replace with your video file path
    output_dir = "output_frames"   # Replace with your desired output directory
    save_frames(video_path, output_dir)