
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('captureButton');
const startCameraButton = document.getElementById('startCameraButton');
const stopCameraButton = document.getElementById('stopCameraButton');
const handSelection = document.getElementById('handSelection');
const letterSelection = document.getElementById('letterSelection');
const imageList = document.getElementById('imageList');
const messageDiv = document.getElementById('message'); // Added a reference to the message div
let stream = null;

// Function to start the camera
function startCamera() {
    if (!stream) {
        navigator.mediaDevices
            .getUserMedia({ video: true })
            .then(function (cameraStream) {
                stream = cameraStream;
                video.srcObject = cameraStream;
                startCameraButton.disabled = true;
                stopCameraButton.disabled = false;
            })
            .catch(function (error) {
                console.error('Error accessing the camera: ', error);
            });
    }
}

// Event listener for the Start Camera button
startCameraButton.addEventListener('click', function () {
    startCamera();
});

// Function to stop the camera
function stopCamera() {
    if (stream) {
        const tracks = stream.getTracks();
        tracks.forEach((track) => track.stop());
        video.srcObject = null;
        stream = null;
        startCameraButton.disabled = false;
        stopCameraButton.disabled = true;
    }
}

// Event listener for the Stop Camera button
stopCameraButton.addEventListener('click', function () {
    stopCamera();
});

// Function to capture and send an image
async function saveCapturedImage(index) {
    return new Promise((resolve, reject) => {
        if (stream) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBlob = canvas.toBlob(function (blob) {
                const formData = new FormData();
                formData.append('image_data', blob, `captured_image_${index}.jpeg`);
                formData.append('hand', handSelection.value);
                formData.append('letter', letterSelection.value);

                const imageElement = document.createElement('img');
                imageElement.src = URL.createObjectURL(blob);

                imageList.appendChild(imageElement);

                fetch('/save_image', {
                    method: 'POST',
                    body: formData,
                })
                    .then((response) => response.json())
                    .then((data) => {
                        console.log(data.message);
                        resolve(blob); // Resolve with the image blob
                    })
                    .catch((error) => {
                        console.error('Error saving image: ', error);
                        reject(error);
                    });
            }, 'image/jpeg', 1.0);
        } else {
            console.error('Camera is not running');
            reject('Camera not running');
        }
    });
}

// Event listener for the Capture button
captureButton.addEventListener('click', async function () {
    startCamera(); // Ensure the camera is started

    if (stream) {
        for (let i = 0; i < 100; i++) {
            await saveCapturedImage(i); // Capture and save 100 images
        }
        // Display the success message after capturing and storing the images
        messageDiv.style.display = 'block';
    }
});
