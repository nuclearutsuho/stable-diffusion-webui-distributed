# stable-diffusion-webui-distributed
# SD WebUI 分布式扩展

This extension enables you to chain multiple webui instances together for txt2img and img2img generation tasks.

这个扩展允许你将多个WebUI实例链接在一起，用于文生图(txt2img)和图生图(img2img)的生成任务。

*For those with **multi-gpu** setups, **yes** this can be used for generation across all of those devices.*

*对于那些拥有**多GPU**设置的用户来说，**是的**，这个扩展可以用于在所有这些设备上进行生成。*

The main goal is minimizing the lag of (high batch size) requests from the **main** sdwui instance.

主要目标是最小化来自主SD WebUI实例的（大批量）请求的延迟。


**Contributions and feedback are much appreciated!**

**欢迎贡献和反馈！**

[![](https://dcbadge.vercel.app/api/server/Jpc8wnftd4)](https://discord.gg/Jpc8wnftd4)

## Installation
## 安装

On the master instance:
在主实例上：
- Go to the extensions tab, and swap to the "available" sub-tab. Then, search "Distributed", and hit install on this extension.
- 转到扩展标签页，切换到"可用"子标签页。然后，搜索"Distributed"，点击安装此扩展。

On each slave instance:
在每个从实例上：
- enable the api by passing `--api` and ensure it is listening by using `--listen`
- ensure all of the models, scripts, and whatever else you think you might request from them is present\
Ie. if you're using sd-1.5 on the controlling instance, then the sd-1.5 model should also be present on each slave instance. Otherwise, the remote will fallback to some other model that **is** present.

- 通过传递`--api`参数启用API，并使用`--listen`参数确保它在监听
- 确保所有模型、脚本以及你可能会请求的其他内容都存在\
例如，如果你在控制实例上使用sd-1.5，那么sd-1.5模型也应该存在于每个从实例上。否则，远程实例将回退到其他**已存在**的模型。

*if you want to easily sync models between your nodes, you might want to use something like [rclone](https://rclone.org/)*

*如果你想在节点之间轻松同步模型，你可以使用类似[rclone](https://rclone.org/)这样的工具*

### Tips
### 提示

- If benchmarking fails, try hitting the **Redo benchmark** button under the script's **Util** tab.
- If any remote is taking far too long to returns its share of the batch, you can hit the **Interrupt** button in the **Util** tab.
- If you think that a worker is being under-utilized, you can adjust the job timeout setting to be higher. However, doing this may be suboptimal in cases where the "slow" machine is **actually** really slow. Alternatively, you may just need to do a re-benchmark or manually edit the config.

- 如果基准测试失败，请尝试点击脚本的**Util**标签页下的**重新基准测试**按钮。
- 如果任何远程实例花费太长时间才返回其批次份额，你可以点击**Util**标签页中的**中断**按钮。
- 如果你认为某个工作节点未被充分利用，你可以调高作业超时设置。但是，在"慢速"机器**确实**很慢的情况下，这样做可能并不理想。另外，你可能只需要重新进行基准测试或手动编辑配置。

### Command-line arguments
### 命令行参数

**--distributed-skip-verify-remotes** Disable verification of remote worker TLS certificates (useful for if you are using self-signed certs like with [auto tls-https](https://github.com/papuSpartan/stable-diffusion-webui-auto-tls-https))\
**--distributed-remotes-autosave** Enable auto-saving of remote worker generations\
**--distributed-debug** Enable debug information

**--distributed-skip-verify-remotes** 禁用远程工作节点TLS证书验证（如果你使用自签名证书，比如使用[auto tls-https](https://github.com/papuSpartan/stable-diffusion-webui-auto-tls-https)时很有用）\
**--distributed-remotes-autosave** 启用远程工作节点生成结果的自动保存\
**--distributed-debug** 启用调试信息
