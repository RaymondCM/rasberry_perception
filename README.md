# rasberry_perception

The rasberry_perception package aims to interleave ROS and deep learning frameworks for perception. If using any of the models in research please contact [Raymond Kirk](https://github.com/RaymondKirk) to obtain the relevant citation and ensure no conflict of interest.

![strawberry_localisation](https://user-images.githubusercontent.com/16948324/76231446-2c98b380-621d-11ea-8624-8e472c2f08f8.gif)

## Installation

This project is dependent on a modified version of [LCAS/bayestracking](LCAS/bayestracking). 

```
cd catkin_ws/src
git clone https://github.com/RaymondKirk/bayestracking
catkin build rasberry_perception
```

## Usage

## Detection Backends

Modular detection backends are available in `rasberry_perception` enabling users to utilise deep learning 
frameworks/non-ros methods to detect objects. This functionality provided via a ros service `GetDetectorResults`. 
This modular approach enables things such as Python3 DL backends in Python2 ros environments.

To run the detection backend service run the command below replacing backend with a listed one below, or your own:

```bash 
rosrun rasberry_perception detection_server.py backend:="" backend_arg1:=""
```

Then you can launch the detector:

```bash
roslaunch rasberry_perception detector.launch colour_ns:='' depth_ns:='' score:=''
```

Alternatively if a `run_$backend.sh` script exists in `scripts/docker_backends/` you can launch both the docker backend
and the detector with the command below:

```bash
roslaunch rasberry_perception detector.launch colour_ns:='' depth_ns:='' score:='' backend:="<your backend>"
```

### Adding a new detection backend 

Adding custom backends such as TensorFlow, PyTorch, Detectron, Onnx etc. to `rasberry_perception` is easy. 

Just create a custom class as shown below, inherit from the base, and register it's backend name in the detection registry. 
Note you have to place the custom class inside the 
[registry file](src/deep_learning_ros/compatibility_layer/registry.py) found here `src/deep_learning_ros/compatibility_layer/registry.py`.
This can be avoided in future releases if we start to amass a large collection of supported backends.


```python
from rasberry_perception.srv import GetDetectorResultsResponse
from deep_learning_ros.compatibility_layer.detection_server import _DetectorResultsServer
from deep_learning_ros.compatibility_layer.registry import DETECTION_REGISTRY

@DETECTION_REGISTRY.register_detection_backend("CustomBackendName")
class CustomVisionBackend(_DetectorResultsServer):
    def __init__(self, custom_arg1, custom_arg2, default_arg1="hello"):
        # Do your custom initialisation logic here (custom imports etc)
        _DetectorResultsServer.__init__(self)

    def get_detector_results(self, request):
        # Implement your custom backend logic here (return a GetDetectorResultsResponse object)
       return GetDetectorResultsResponse()
```

When launching the detection server via `rosrun` you can pass in arguments to your custom backend as you would usually.
The node will fail if you do not pass any non-default arguments such as `custom_arg1` and `custom_arg2` in the example.

```bash
rosrun rasberry_perception detection_server.py _custom_arg1:="a1" _custom_arg2:="a2" _default_arg1"="world"
```

## Docker

First of all build the base docker image using your current cloned repo.

```bash
docker build -f ./docker/base/Dockerfile $(rospack find rasberry_perception) -t rasberry_perception:base

# or for gpu
docker build -f ./docker/base_gpu/Dockerfile $(rospack find rasberry_perception) -t rasberry_perception:base_gpu
```

Build the backend of your choice.

```bash
bash docker/mmdetection/get_mmdetection.sh
# Move your model and config files to docker/mmdetection
docker build -t rasberry_perception:mmdetection docker/mmdetection/

# Run the backend 
docker run --network host --gpus all -it rasberry_perception:mmdetection /start
```
