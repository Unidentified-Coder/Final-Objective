import cv2
from img_input import img_input # python script imported from another file 

img_input()

# Trained dataset
cascade_src = ('cars.xml')
car_cascade = cv2.CascadeClassifier(cascade_src)

# Save image path as variable for easier access
img = cv2.imread("image-Folder/Shared_image.png")

# Throws an error, Exit code if img is not available 
if img is None:
    print("Error: Image not found or cannot be loaded")
    exit()

# Convert image into grey scale for identification 
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Draws boxes on detected vehicles
cars = car_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(30,30))

# Initialise the vehicle count variable to be used within for loop
vehicle_count = 0
for (x,y,w,h) in cars:
    cv2.rectangle(img,(x,y),(x+y,y+h),(0,0,250),2)
    vehicle_count += 1

height, width, _ = img.shape

text_x = width - 250
text_y = height - 250

# Places text on image to show the amount of vehicles counted in process
cv2.putText(img, f"Vehicles: {vehicle_count}",(text_x,text_y), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,255),2,cv2.LINE_AA )

# Output the result in a windows app format 
cv2.imshow('Detected Vehicles', img)

# release the contents by freeing up memory used in operation 
cv2.waitKey(0)
cv2.destroyAllWindows

