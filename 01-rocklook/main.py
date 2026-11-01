import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Could not open the camera.")
else:
    while True:
        success, frame = camera.read()

        if not success:
            print("Could not read a camera frame.")
            break

        cv2.imshow("RockLook - press Q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

camera.release()
cv2.destroyAllWindows()