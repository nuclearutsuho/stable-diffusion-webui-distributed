from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Benchmark_Payload(BaseModel):
    prompt: str = Field(default="A herd of cows grazing at the bottom of a sunny valley")
    negative_prompt: str = Field(default="")
    steps: int = Field(default=20)
    width: int = Field(default=512)
    height: int = Field(default=512)
    batch_size: int = Field(default=1)

class Worker_Model(BaseModel):
    avg_ipm: Optional[float] = Field(
        title='Average Speed',
        description='the speed of a device measured in ipm(images per minute)',
        ge=0
    )
    master: bool = Field(description="whether or not an instance is the master(local) node", default=False)
    address: Optional[str] = Field(default='localhost')
    port: Optional[int] = Field(default=7860, ge=0, le=65535)
    eta_percent_error: Optional[List[float]] = Field(
        title='ETA Percent Error',
        description='A list of eta prediction percent errors from the last session',
        default=list()
    )
    tls: Optional[bool] = Field(
        title='Transport Layer Security',
        description='Whether or not to make requests to a worker securely',
        default=False
    )
    state: Optional[Any] = Field(default=1, description="The last known state of this worker")
    user: Optional[str] = Field(description="The username to be used when authenticating with this worker", default=None)
    password: Optional[str] = Field(description="The password to be used when authenticating with this worker", default=None)
    pixel_cap: Optional[int] = Field(default=-1, description="Max amount of pixels to allow one worker to handle at the same time. -1 means there is no limit")

class ConfigModel(BaseModel):
    workers: List[Dict[str, Worker_Model]]
    benchmark_payload: Benchmark_Payload = Field(
        default=Benchmark_Payload,
        description='the payload used when benchmarking a node'
    )
    job_timeout: Optional[int] = Field(default=3)
    enabled: Optional[bool] = Field(description="Whether the extension as a whole should be active or disabled", default=True)
    enabled_i2i: Optional[bool] = Field(description="Same as above but for image to image", default=True)
    complement_production: Optional[bool] = Field(description="Whether to generate complementary images to prevent under-utilizing hardware", default=True)
    step_scaling: Optional[bool] = Field(description="Whether to downscale requested steps in order to meet time constraints", default=False)
