#!/usr/bin/env python3
"""
自动生成的 Wiki 内容文件

此文件由 tools/generate_wiki_ui.py 从 documents/wiki.md 生成。
请勿手动修改此文件，修改 wiki.md 后重新运行生成器：

    python tools/generate_wiki_ui.py
"""

# CSS 样式表 - 亮色主题 (仅使用 Qt Rich Text 支持的属性)
WIKI_CSS_LIGHT = r"""
body { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 14px; color: #2b2b2b; }
h1 { font-size: 24px; font-weight: 600; color: #0078d4; border-bottom: 2px solid #0078d4; padding-bottom: 8px; margin-top: 6px; margin-bottom: 18px; }
h2 { font-size: 19px; font-weight: 600; color: #1a1a1a; border-left: 4px solid #0078d4; padding-left: 10px; margin-top: 30px; margin-bottom: 14px; }
h3 { font-size: 16px; font-weight: 600; color: #333333; margin-top: 24px; margin-bottom: 10px; }
h4 { font-size: 15px; font-weight: 600; color: #555555; margin-top: 16px; margin-bottom: 8px; }
h5 { font-size: 14px; font-weight: 600; color: #666666; }
h6 { font-size: 13px; font-weight: 600; color: #888888; }
p { margin: 8px 0; color: #333333; line-height: 1.8; }
a { color: #0078d4; text-decoration: none; }
img { margin: 12px 0; border: 1px solid #e0e0e0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; border: 1px solid #dddddd; }
th { background-color: #f0f4f8; color: #1a1a1a; font-weight: 600; padding: 8px 12px; border: 1px solid #dddddd; text-align: left; }
td { padding: 6px 12px; border: 1px solid #dddddd; color: #333333; }
code { background-color: #f0f0f0; color: #0078d4; padding: 1px 5px; font-family: "Consolas", "Courier New", monospace; font-size: 12px; }
pre { background-color: #f8f8f8; border: 1px solid #e0e0e0; border-left: 3px solid #0078d4; padding: 12px 14px; margin: 10px 0; }
pre code { background-color: transparent; color: #333333; padding: 0; font-size: 13px; }
blockquote { border-left: 3px solid #0078d4; background-color: #eef6fd; margin: 10px 0; padding: 8px 14px; color: #555555; }
blockquote p { color: #555555; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }
strong { font-weight: 600; color: #1a1a1a; }
em { color: #666666; }
ul { margin: 8px 0; padding-left: 24px; }
ol { margin: 8px 0; padding-left: 24px; }
li { margin: 4px 0; color: #333333; }
del { color: #999999; }
kbd { background-color: #f5f5f5; border: 1px solid #cccccc; padding: 1px 5px; font-size: 12px; font-family: monospace; }
"""

# CSS 样式表 - 暗色主题
WIKI_CSS_DARK = r"""
body { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 14px; color: #d6d6d6; }
h1 { font-size: 24px; font-weight: 600; color: #4cc2ff; border-bottom: 2px solid #4cc2ff; padding-bottom: 8px; margin-top: 6px; margin-bottom: 18px; }
h2 { font-size: 19px; font-weight: 600; color: #f0f0f0; border-left: 4px solid #4cc2ff; padding-left: 10px; margin-top: 30px; margin-bottom: 14px; }
h3 { font-size: 16px; font-weight: 600; color: #dddddd; margin-top: 24px; margin-bottom: 10px; }
h4 { font-size: 15px; font-weight: 600; color: #aaaaaa; margin-top: 16px; margin-bottom: 8px; }
h5 { font-size: 14px; font-weight: 600; color: #999999; }
h6 { font-size: 13px; font-weight: 600; color: #888888; }
p { margin: 8px 0; color: #cccccc; line-height: 1.8; }
a { color: #4cc2ff; text-decoration: none; }
img { margin: 12px 0; border: 1px solid #404040; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; border: 1px solid #404040; }
th { background-color: #2a2a2a; color: #f0f0f0; font-weight: 600; padding: 8px 12px; border: 1px solid #404040; text-align: left; }
td { padding: 6px 12px; border: 1px solid #383838; color: #cccccc; }
code { background-color: #2d2d2d; color: #4cc2ff; padding: 1px 5px; font-family: "Consolas", "Courier New", monospace; font-size: 12px; }
pre { background-color: #1e1e1e; border: 1px solid #383838; border-left: 3px solid #4cc2ff; padding: 12px 14px; margin: 10px 0; }
pre code { background-color: transparent; color: #d4d4d4; padding: 0; font-size: 13px; }
blockquote { border-left: 3px solid #4cc2ff; background-color: #1a2632; margin: 10px 0; padding: 8px 14px; color: #aaaaaa; }
blockquote p { color: #aaaaaa; }
hr { border: none; border-top: 1px solid #404040; margin: 24px 0; }
strong { font-weight: 600; color: #ffffff; }
em { color: #999999; }
ul { margin: 8px 0; padding-left: 24px; }
ol { margin: 8px 0; padding-left: 24px; }
li { margin: 4px 0; color: #cccccc; }
del { color: #666666; }
kbd { background-color: #333333; border: 1px solid #555555; padding: 1px 5px; font-size: 12px; font-family: monospace; }
"""

# HTML body 内容 (图片已添加 width 属性)
WIKI_HTML = r"""
<h1>NBS-to-Minecraftsave 完整使用指南</h1>
<blockquote>
<p><strong>NBS-to-Minecraftsave</strong> 是一款强大的转换工具，可将 Note Block Studio 制作的音乐文件 (<code>.nbs</code>) 转换为 Minecraft 中可播放的格式。</p>
</blockquote>
<hr />
<h2>一、环境准备</h2>
<h3>1.1 系统要求</h3>
<table>
<thead>
<tr>
<th style="text-align: left;">项目</th>
<th style="text-align: left;">要求</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>操作系统</strong></td>
<td style="text-align: left;">Windows 10/11、macOS、Linux 均可 (只要能运行 python 就行)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Python 版本</strong></td>
<td style="text-align: left;">Python 3.8 及以上版本</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Minecraft 版本</strong></td>
<td style="text-align: left;">Java Edition 1.13 至 26.1.1</td>
</tr>
</tbody>
</table>
<h3>1.2 必要软件安装</h3>
<h4>步骤 1：安装 Python</h4>
<ol>
<li>访问 <a href="https://www.python.org/downloads/">Python 官网</a></li>
<li>下载 Python 3.8 或更高版本</li>
<li>安装时<strong>务必勾选 "Add Python to PATH"</strong>(添加到环境变量)</li>
<li>打开命令提示符 (PowerShell)，输入以下命令验证安装：</li>
</ol>
<p><code>sh
   python --version</code></p>
<p><strong>若成功安装，应显示版本号</strong>：</p>
<p><code>ansi
   Python 3.x.x</code></p>
<h4>步骤 2：安装 Git(可选)</h4>
<blockquote>
<p>💡 仅在需要通过 Git 克隆仓库时安装</p>
</blockquote>
<ol>
<li>访问 <a href="https://git-scm.com/download/win">Git 官网</a></li>
<li>下载并安装 Git</li>
<li>安装完成后验证：</li>
</ol>
<p><code>sh
   git --version</code></p>
<hr />
<h2>二、下载与安装</h2>
<h3>2.1 方式一：通过 Git 克隆 (推荐)</h3>
<p>打开 PowerShell，运行以下命令：</p>
<pre><code class="language-sh"># 克隆仓库到本地
git clone https://github.com/sensen1234/NBS-to-minecraftsave.git

# 进入项目目录
cd NBS-to-minecraftsave
</code></pre>
<h3>2.2 方式二：手动下载</h3>
<ol>
<li>访问项目 GitHub 页面 (<a href="https://github.com/sensen1234/NBS-to-minecraftsave">https://github.com/sensen1234/NBS-to-minecraftsave</a>)</li>
<li>点击 Releases<br />
<img width="500" alt="Releases" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image.png" /></li>
<li>找到最新版，点击 Assets 里面的 Source code 进行下载<br />
<img width="500" alt="Download ZIP" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/efcc02de891be4ea97d4dd1bc111b846.png" /></li>
<li>解压下载的文件到任意任意目录 (尽量为英文目录)</li>
</ol>
<h3>2.3 安装依赖</h3>
<p>程序需要以下 Python 库：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">库名称</th>
<th style="text-align: left;">版本要求</th>
<th style="text-align: left;">作用描述</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>pynbs</code></td>
<td style="text-align: left;">最新稳定版</td>
<td style="text-align: left;">读取和解析 NBS 文件格式</td>
</tr>
<tr>
<td style="text-align: left;"><code>mcschematic</code></td>
<td style="text-align: left;">最新稳定版</td>
<td style="text-align: left;">生成 Minecraft 结构文件</td>
</tr>
<tr>
<td style="text-align: left;"><code>PyQt6</code></td>
<td style="text-align: left;">最新稳定版</td>
<td style="text-align: left;">提供图形用户界面框架</td>
</tr>
</tbody>
</table>
<p>进入项目目录后，运行以下命令安装所有依赖：</p>
<pre><code class="language-sh">uv sync
</code></pre>
<blockquote>
<p>💡 <strong>Tips</strong>：如果下载速度慢，可以使用国内镜像源：</p>
<p><code>sh
uv sync -i https://pypi.tuna.tsinghua.edu.cn/simple</code></p>
</blockquote>
<h3>2.4 验证安装</h3>
<p>运行以下命令验证安装是否成功：\<br />
(需要在项目目录下运行)</p>
<pre><code class="language-sh"># 测试 GUI 模式
uv run src/app.py

# 或测试 CLI 模式
uv run src/cli.py
</code></pre>
<hr />
<h2>三、配置说明</h2>
<blockquote>
<p>程序支持两种使用方式：<strong>GUI 图形界面</strong>(推荐新手) 和 <strong>CLI 命令行</strong>(适合高级用户和自动化脚本)。</p>
</blockquote>
<h3>3.1 GUI 模式配置</h3>
<h4>启动 GUI</h4>
<pre><code class="language-sh">uv run src/app.py
</code></pre>
<h4>界面结构</h4>
<p>程序界面分为三个主要标签页：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">标签页</th>
<th style="text-align: left;">图标</th>
<th style="text-align: left;">功能说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>基础设置</strong></td>
<td style="text-align: left;">⚙️</td>
<td style="text-align: left;">文件输入输出、版本选择、格式配置</td>
</tr>
<tr>
<td style="text-align: left;"><strong>轨道组</strong></td>
<td style="text-align: left;">🛤️</td>
<td style="text-align: left;">轨道分组管理、坐标规划、方块配置</td>
</tr>
<tr>
<td style="text-align: left;"><strong>运行日志</strong></td>
<td style="text-align: left;">📝</td>
<td style="text-align: left;">实时显示转换进度和错误信息</td>
</tr>
</tbody>
</table>
<hr />
<h4>基础设置详解</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">配置项</th>
<th style="text-align: left;">说明</th>
<th style="text-align: left;">操作方式</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>文件输入</strong></td>
<td style="text-align: left;">选择要转换的 <code>.nbs</code> 文件</td>
<td style="text-align: left;">点击"浏览..."按钮选择文件</td>
</tr>
<tr>
<td style="text-align: left;"><strong>输出路径</strong></td>
<td style="text-align: left;">设置生成文件的保存路径</td>
<td style="text-align: left;">自动根据输入文件名填充，可手动修改</td>
</tr>
<tr>
<td style="text-align: left;"><strong>目标游戏版本</strong></td>
<td style="text-align: left;">选择 Minecraft Java Edition 版本</td>
<td style="text-align: left;">从下拉菜单选择对应版本</td>
</tr>
<tr>
<td style="text-align: left;"><strong>输出格式</strong></td>
<td style="text-align: left;">选择生成文件类型</td>
<td style="text-align: left;">二选一：Schem 或 Mcfunction</td>
</tr>
</tbody>
</table>
<p><strong>输出格式对比</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">格式</th>
<th style="text-align: left;">文件扩展名</th>
<th style="text-align: left;">依赖模组</th>
<th style="text-align: left;">适用场景</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">WorldEdit Schematic</td>
<td style="text-align: left;"><code>.schem</code></td>
<td style="text-align: left;">需要 WorldEdit</td>
<td style="text-align: left;">快速导入、可视化编辑</td>
</tr>
<tr>
<td style="text-align: left;">Minecraft Function</td>
<td style="text-align: left;"><code>.mcfunction</code></td>
<td style="text-align: left;">无需模组 (原版支持)</td>
<td style="text-align: left;">原版部署</td>
</tr>
</tbody>
</table>
<hr />
<h4>轨道组配置详解</h4>
<blockquote>
<p>⭐ <strong>这是程序最核心的配置区域</strong>，用于管理音符轨道的空间布局。</p>
</blockquote>
<p><strong>表格列说明</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">列名</th>
<th style="text-align: left;">说明</th>
<th style="text-align: left;">示例值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>ID</strong></td>
<td style="text-align: left;">轨道组唯一标识符</td>
<td style="text-align: left;"><code>0</code>, <code>1</code>, <code>2</code>...</td>
</tr>
<tr>
<td style="text-align: left;"><strong>基准 X</strong></td>
<td style="text-align: left;">该组在 Minecraft 世界中的 X 坐标</td>
<td style="text-align: left;"><code>0</code>, <code>100</code>, <code>-50</code>...</td>
</tr>
<tr>
<td style="text-align: left;"><strong>基准 Y</strong></td>
<td style="text-align: left;">该组在 Minecraft 世界中的 Y 坐标 (高度)</td>
<td style="text-align: left;"><code>64</code>, <code>100</code>...</td>
</tr>
<tr>
<td style="text-align: left;"><strong>基准 Z</strong></td>
<td style="text-align: left;">该组在 Minecraft 世界中的 Z 坐标</td>
<td style="text-align: left;"><code>0</code>, <code>200</code>...</td>
</tr>
<tr>
<td style="text-align: left;"><strong>坐标规划</strong></td>
<td style="text-align: left;">打开可视化坐标选择器</td>
<td style="text-align: left;">点击 📍 选点 按钮</td>
</tr>
<tr>
<td style="text-align: left;"><strong>轨道 ID</strong></td>
<td style="text-align: left;">NBS 文件中的轨道编号 (多个用逗号分隔)</td>
<td style="text-align: left;"><code>0,1,2,3,4,5,6</code></td>
</tr>
<tr>
<td style="text-align: left;"><strong>基础方块</strong></td>
<td style="text-align: left;">构成平台的主体方块类型</td>
<td style="text-align: left;"><code>minecraft:iron_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><strong>覆盖方块</strong></td>
<td style="text-align: left;">覆盖在平台顶层的方块</td>
<td style="text-align: left;"><code>minecraft:iron_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><strong>生成模式</strong></td>
<td style="text-align: left;">生成结构的样式</td>
<td style="text-align: left;"><code>default</code> 或 <code>staircase</code></td>
</tr>
</tbody>
</table>
<h4>详细说明</h4>
<ul>
<li>ID：</li>
</ul>
<p>每个 ID 对应一个<code>轨道组</code>，如 0 对应第一个轨道组，2 对应第二个，以此类推  </p>
<p>通常不需要修改该数值</p>
<ul>
<li>基准 X、Y、Z：</li>
</ul>
<p>每个轨道组的<strong>第一个方块 (cover 或音符盒)</strong>在 Minecraft 世界中的坐标，用于确定音符平台和红石线的位置。<br />
  - 若选择的为 schem 模式，<strong>该处对应的为相对于 (0,0,0) 坐标的向量位置</strong></p>
<pre><code>如：基准X=100,基准Y=64,基准Z=0 表示轨道组的**第一个方块(cover或音符盒)**在(100,64,0)位置生成  
其中(0,0,0)为Schematic文件的原点，与Minecraft世界原点不同(也就是你站在地上，输入schem load对应的那个坐标)  
推荐0轨道(ID=0)设定为voice(Main Rhythm)轨道，其轨道的坐标设置为(0,0,0)
</code></pre>
<ul>
<li>
<p>若选择的为 mcfunction 模式，<strong>该处对应的为 Minecraft 中的坐标</strong><br />
    如：基准 X=100，基准 Y=64，基准 Z=0 表示轨道组的<strong>第一个方块 (cover 或音符盒)</strong>在 (100,64,0) 位置生成<br />
    (不难理解，因为 mcfunction 模式为一大堆命令，命令执行的为<code>setblock x y z 方块类型</code>，故 XYZ 为 Minecraft 中的坐标，与 Schematic 文件的坐标不同)</p>
</li>
<li>
<p>坐标规划 (GUI 选点)：</p>
</li>
</ul>
<p>点击"📍 选点"按钮，打开可视化界面在网格上拖动选择坐标 (选择的为轨道组的 XY 坐标，不支持 Z 坐标)<br />
  (PS：程序本身就是默认为向东边生成，所以 GUI 选点不能设定 Z 坐标)</p>
<ul>
<li>轨道 ID：<br />
  每个轨道组包含多个轨道，每个轨道对应一个音符平台和红石线。<br />
  该处为 NBS 文件中的轨道编号，多个轨道编号之间用逗号分隔。</li>
</ul>
<p>如：轨道 ID=0,1,2,3,4,5,6 表示轨道组包含 7 个轨道，编号为 0、1、2、3、4、5、6<br />
  其中，轨道<code>ID=0</code>对应<code>NBS中的第一个轨道</code> 1 对应第 2 个 以此类推。</p>
<ul>
<li>基础方块、覆盖方块：</li>
</ul>
<p>每个轨道组的音符平台和红石线的方块类型，基础方块用于放置在音符盒下一层中的方块，覆盖方块用于放置在音符盒同层的方块。<br />
  该处为 Minecraft 中的方块类型，如<code>minecraft:iron_block</code>、<code>minecraft:stone</code>等。</p>
<ul>
<li>生成模式：</li>
</ul>
<p>生成结构的样式，<code>default</code>为默认模式，<code>staircase</code>为阶梯向下模式。默认模式为<code>default</code>。<br />
  - <code>default</code>模式：所有音符平台和红石线保持在同一水平高度。<br />
  - <code>staircase</code>模式：当左右偏移 ≥ 3 时，音符平台逐级向下阶梯式生成。</p>
<p><strong>生成模式对比</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">模式</th>
<th style="text-align: left;">名称</th>
<th style="text-align: left;">特点</th>
<th style="text-align: left;">适用场景</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>default</code></td>
<td style="text-align: left;">默认模式</td>
<td style="text-align: left;">所有音符平台和红石线保持在同一水平高度</td>
<td style="text-align: left;">大多数情况</td>
</tr>
<tr>
<td style="text-align: left;"><code>staircase</code></td>
<td style="text-align: left;">阶梯向下模式</td>
<td style="text-align: left;">当左右偏移 ≥ 3 时，音符平台逐级向下阶梯式生成</td>
<td style="text-align: left;">大型音乐作品、立体视觉效果</td>
</tr>
</tbody>
</table>
<hr />
<h3>3.2 命令行模式配置</h3>
<h4>运行命令 (记得在修改完配置后运行！)</h4>
<pre><code class="language-sh">uv run src/cli.py
</code></pre>
<h4>配置文件位置</h4>
<p><code>src/nbs2save/core/config.py</code></p>
<h4>全局生成配置 (<code>GENERATE_CONFIG</code>)</h4>
<pre><code class="language-python">GENERATE_CONFIG = {
    # 指定生成的 schematic 文件的 Minecraft 版本
    # 仅在输出格式为 schematic 时生效
    # 可选值参考 mcschematic.Version 枚举
    'data_version': Version.JE_1_21_4,

    # 指定要转换的 NBS 文件路径
    'input_file': 'test.nbs',

    # 指定输出格式类型
    # 可选值：'schematic' 或 'mcfunction'
    'type': 'schematic',

    # 指定输出文件的名称 (不包含扩展名)
    # 程序会自动添加相应的扩展名
    'output_file': 'test'
}
</code></pre>
<p><strong>参数详解</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">参数名</th>
<th style="text-align: left;">数据类型</th>
<th style="text-align: left;">说明</th>
<th style="text-align: left;">示例值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>data_version</code></td>
<td style="text-align: left;"><code>Version</code></td>
<td style="text-align: left;">目标 Minecraft 版本，影响 schematic 文件的兼容性</td>
<td style="text-align: left;"><code>Version.JE_1_21_4</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>input_file</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">NBS 文件的完整路径 (相对或绝对路径均可)</td>
<td style="text-align: left;"><code>'test.nbs'</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>type</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">输出格式类型</td>
<td style="text-align: left;"><code>'schematic'</code> 或 <code>'mcfunction'</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>output_file</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">输出文件名 (不包含扩展名)</td>
<td style="text-align: left;"><code>'test'</code></td>
</tr>
</tbody>
</table>
<hr />
<h4>轨道组配置 (<code>GROUP_CONFIG</code>)</h4>
<pre><code class="language-python">GROUP_CONFIG = {
    # 轨道组 0 的配置
    0: {
        # 基准坐标 (x, y, z)，必须是字符串类型
        'base_coords': (&quot;0&quot;, &quot;0&quot;, &quot;0&quot;),

        # 该组包含的轨道 ID 列表
        'layers': [0, 1, 2, 3, 4, 5, 6],

        # 方块配置
        'block': {
            # 基础平台方块
            'base': 'minecraft:iron_block',
            # 顶部覆盖方块
            'cover': 'minecraft:iron_block'
        },

        # 生成模式：'default' 或 'staircase'
        'generation_mode': 'default'
    },
}
</code></pre>
<p><strong>参数详解</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">参数名</th>
<th style="text-align: left;">数据类型</th>
<th style="text-align: left;">说明</th>
<th style="text-align: left;">示例值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>base_coords</code></td>
<td style="text-align: left;"><code>tuple(str, str, str)</code></td>
<td style="text-align: left;">轨道组的第一个方块 (cover 或音符盒) 在 Minecraft 世界中的起始位置 <code>(X, Y, Z)</code>，<strong>字符串类型</strong></td>
<td style="text-align: left;"><code>("0", "64", "0")</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>layers</code></td>
<td style="text-align: left;"><code>list[int]</code></td>
<td style="text-align: left;">NBS 文件中的轨道 ID 列表，对应 NBS 中的轨道编号如 0 对应 NBS 的第一个轨道</td>
<td style="text-align: left;"><code>[0, 1, 2, 3]</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>block.base</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">基础平台方块 (放置在音符盒下一层的方块)</td>
<td style="text-align: left;"><code>'minecraft:iron_block'</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>block.cover</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">顶部覆盖方块 (放置在音符盒同层的方块，用于隐藏红石线路)</td>
<td style="text-align: left;"><code>'minecraft:iron_block'</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>generation_mode</code></td>
<td style="text-align: left;"><code>str</code></td>
<td style="text-align: left;">生成模式：<code>default</code>(默认，同一水平高度) 或 <code>staircase</code>(阶梯向下)</td>
<td style="text-align: left;"><code>'default'</code> 或 <code>'staircase'</code></td>
</tr>
</tbody>
</table>
<blockquote>
<p>💡 <strong>坐标说明</strong>：</p>
<ul>
<li>若输出格式为 <strong>schematic</strong>：<code>base_coords</code> 为相对于 <code>(0,0,0)</code> 的向量位置，与 Minecraft 世界原点不同</li>
<li>若输出格式为 <strong>mcfunction</strong>：<code>base_coords</code> 为 Minecraft 中的绝对坐标</li>
</ul>
<p>💡 <strong>Y 坐标建议</strong>：设置在 <code>64</code> 或更高，避免结构生成在地底。</p>
</blockquote>
<hr />
<h3>3.3 常量配置</h3>
<blockquote>
<p>⚠️ 通常无需修改，除非需要添加自定义音色。</p>
</blockquote>
<p><strong>文件位置</strong>：<code>src/nbs2save/core/constants.py</code></p>
<h4>乐器映射 (<code>INSTRUMENT_MAPPING</code>)</h4>
<p>定义 NBS 乐器 ID 到 Minecraft 音符盒音色的对应关系：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">ID</th>
<th style="text-align: left;">NBS 乐器</th>
<th style="text-align: left;">Minecraft 音色标识</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>0</code></td>
<td style="text-align: left;">钢琴 (竖琴)</td>
<td style="text-align: left;"><code>harp</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>1</code></td>
<td style="text-align: left;">贝斯</td>
<td style="text-align: left;"><code>bass</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>2</code></td>
<td style="text-align: left;">底鼓</td>
<td style="text-align: left;"><code>basedrum</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>3</code></td>
<td style="text-align: left;">小军鼓</td>
<td style="text-align: left;"><code>snare</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>4</code></td>
<td style="text-align: left;">铜钹</td>
<td style="text-align: left;"><code>hat</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>5</code></td>
<td style="text-align: left;">吉他</td>
<td style="text-align: left;"><code>guitar</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>6</code></td>
<td style="text-align: left;">长笛</td>
<td style="text-align: left;"><code>flute</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>7</code></td>
<td style="text-align: left;">钟琴</td>
<td style="text-align: left;"><code>bell</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>8</code></td>
<td style="text-align: left;">风铃</td>
<td style="text-align: left;"><code>chime</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>9</code></td>
<td style="text-align: left;">木琴</td>
<td style="text-align: left;"><code>xylophone</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>10</code></td>
<td style="text-align: left;">铁木琴</td>
<td style="text-align: left;"><code>iron_xylophone</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>11</code></td>
<td style="text-align: left;">牛铃</td>
<td style="text-align: left;"><code>cow_bell</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>12</code></td>
<td style="text-align: left;">迪吉里杜管</td>
<td style="text-align: left;"><code>didgeridoo</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>13</code></td>
<td style="text-align: left;">比特</td>
<td style="text-align: left;"><code>bit</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>14</code></td>
<td style="text-align: left;">班卓琴</td>
<td style="text-align: left;"><code>banjo</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>15</code></td>
<td style="text-align: left;">电钢琴</td>
<td style="text-align: left;"><code>pling</code></td>
</tr>
</tbody>
</table>
<h4>乐器方块映射 (<code>INSTRUMENT_BLOCK_MAPPING</code>)</h4>
<p>定义不同音色需要放置的方块类型：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">乐器 ID</th>
<th style="text-align: left;">乐器名称</th>
<th style="text-align: left;">下方块类型</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>0</code></td>
<td style="text-align: left;">钢琴</td>
<td style="text-align: left;"><code>minecraft:dirt</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>1</code></td>
<td style="text-align: left;">贝斯</td>
<td style="text-align: left;"><code>minecraft:oak_planks</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>2</code></td>
<td style="text-align: left;">底鼓</td>
<td style="text-align: left;"><code>minecraft:stone</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>3</code></td>
<td style="text-align: left;">小军鼓</td>
<td style="text-align: left;"><code>minecraft:sand</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>4</code></td>
<td style="text-align: left;">铜钹</td>
<td style="text-align: left;"><code>minecraft:glass</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>5</code></td>
<td style="text-align: left;">吉他</td>
<td style="text-align: left;"><code>minecraft:white_wool</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>6</code></td>
<td style="text-align: left;">长笛</td>
<td style="text-align: left;"><code>minecraft:clay</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>7</code></td>
<td style="text-align: left;">钟琴</td>
<td style="text-align: left;"><code>minecraft:gold_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>8</code></td>
<td style="text-align: left;">风铃</td>
<td style="text-align: left;"><code>minecraft:packed_ice</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>9</code></td>
<td style="text-align: left;">木琴</td>
<td style="text-align: left;"><code>minecraft:bone_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>10</code></td>
<td style="text-align: left;">铁木琴</td>
<td style="text-align: left;"><code>minecraft:iron_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>11</code></td>
<td style="text-align: left;">牛铃</td>
<td style="text-align: left;"><code>minecraft:soul_sand</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>12</code></td>
<td style="text-align: left;">迪吉里杜管</td>
<td style="text-align: left;"><code>minecraft:pumpkin</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>13</code></td>
<td style="text-align: left;">比特</td>
<td style="text-align: left;"><code>minecraft:emerald_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>14</code></td>
<td style="text-align: left;">班卓琴</td>
<td style="text-align: left;"><code>minecraft:hay_block</code></td>
</tr>
<tr>
<td style="text-align: left;"><code>15</code></td>
<td style="text-align: left;">电钢琴</td>
<td style="text-align: left;"><code>minecraft:glowstone</code></td>
</tr>
</tbody>
</table>
<h4>音高映射 (<code>NOTEPITCH_MAPPING</code>)</h4>
<p>将 MIDI 键值 (<code>33-57</code>) 映射到 Minecraft 音符盒音高 (<code>0-24</code>)。</p>
<hr />
<h2>五、生成示例&amp;高级生成</h2>
<h3>5.1 多轨道组管理</h3>
<p>该模式适用于制作大型红石音乐，将不同乐器或声部放置在不同位置。<br />
若需要生成多轨则需要配置不同的轨道组。(ID=0,1,2,3,4,5,6 等等)</p>
<h4>配置示例 (cil 模式 GUI 同理)</h4>
<pre><code class="language-python">GROUP_CONFIG = {
    # 主旋律组
    0: {
        'base_coords': (&quot;0&quot;, &quot;64&quot;, &quot;0&quot;),
        'layers': [0, 1, 2, 3],
        'block': {
            'base': 'minecraft:iron_block',
            'cover': 'minecraft:gold_block'
        },
        'generation_mode': 'default'
    },
    # 伴奏组
    1: {
        'base_coords': (&quot;3&quot;, &quot;64&quot;, &quot;0&quot;),
        'layers': [4, 5, 6],
        'block': {
            'base': 'minecraft:stone',
            'cover': 'minecraft:iron_block'
        },
        'generation_mode': 'staircase'
    }
}

#比如我这里配置了两个 GROUP
#0 号 GROUP 是主旋律组，1 号 GROUP 是伴奏组，我可以把 NBS 中的轨道 0,1,2,3,4,5,6 分别对应到 0 号 GROUP 和 1 号 GROUP 中
#这时候生成出来的就是两条轨道组，来实现大型红石音乐制作
</code></pre>
<p><img width="500" alt="alt text" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image-1.png" /></p>
<p>通过配置 GROUP 可以实现如上图一样的效果，来实现大型红石音乐制作</p>
<hr />
<h3>5.2 声像偏移 (Panning)</h3>
<p>NBS 文件中的声像设置会影响音符在 Minecraft 中的 <strong>Z 轴位置</strong>。</p>
<h4>工作原理</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">NBS 声像值</th>
<th style="text-align: left;">Minecraft Z 轴偏移</th>
<th style="text-align: left;">方向</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>0</code></td>
<td style="text-align: left;"><code>0</code> 格</td>
<td style="text-align: left;">中央 (主干道)</td>
</tr>
<tr>
<td style="text-align: left;"><code>30</code></td>
<td style="text-align: left;"><code>+3</code> 格</td>
<td style="text-align: left;">右侧</td>
</tr>
<tr>
<td style="text-align: left;"><code>-50</code></td>
<td style="text-align: left;"><code>-5</code> 格</td>
<td style="text-align: left;">左侧</td>
</tr>
<tr>
<td style="text-align: left;"><code>-53</code></td>
<td style="text-align: left;"><code>-5</code> 格</td>
<td style="text-align: left;">左侧</td>
</tr>
</tbody>
</table>
<p><strong>转换公式</strong>：</p>
<p><code>Z 轴偏移格数 = round(NBS 声像值 ÷ 10)</code></p>
<p>这里的<code>round</code>函数用于四舍五入，确保结果为整数。<br />
声像值并非轨道声像，而是音符的声像值。<br />
(即：同一轨道内的不同音符可以拥有各自独立的声像值，并非整个轨道统一设置)</p>
<h4>示例效果</h4>
<p>如果在 NBS 中设置某个音符的声像为 <strong>左声道 20</strong>：</p>
<pre><code class="language-txt">│       ■
│       ■
│   □ ■ ■
│       ■        ↑(中继器朝向)
</code></pre>
<blockquote>
<p>说明：<code>□</code> 表示音符盒，会相对于主干结构左边 <strong>第 2 格</strong> 生成。</p>
</blockquote>
<p><strong>示例图片</strong>：<br />
<img width="500" alt="alt text" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image-2.png" /><br />
如上图所示，将 NBS 切换到<code>声道模式</code>，这里的两个红色箭头所指的<code>L40</code>表示左声道 4 格子，<code>R40</code>表示右声道 4 格子。<br />
生成所对应的位置应如下图<br />
<img width="500" alt="alt text" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image-3.png" /></p>
<h4>⚠️ 重要限制</h4>
<blockquote>
<p>NBS 中<strong>整个轨道的声像偏移设置</strong>无法被程序识别，只能识别<strong>单个音符的声像设置</strong>。<br />
<em>其实也是个好事，因为这样可以实现更复杂的声像分布效果。</em></p>
</blockquote>
<hr />
<h3>5.3 生成模式详解</h3>
<h4>默认模式 (<code>default</code>)</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">特点</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">结构</td>
<td style="text-align: left;">所有音符平台和红石线在同一水平高度</td>
</tr>
<tr>
<td style="text-align: left;">复杂度</td>
<td style="text-align: left;">结构简单，适合大多数情况</td>
</tr>
<tr>
<td style="text-align: left;">维护性</td>
<td style="text-align: left;">易于观察和修改</td>
</tr>
</tbody>
</table>
<p>如图所示：<br />
<img width="500" alt="alt text" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image-4.png" /></p>
<h4>阶梯向下模式 (<code>staircase</code>)</h4>
<p><strong>启用条件</strong>：当声像偏移 <strong>≥ 3</strong> 时自动启用阶梯效果</p>
<p><strong>效果特点</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">层级</th>
<th style="text-align: left;">位置</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>主干道</strong></td>
<td style="text-align: left;"><code>base_y</code> 层</td>
<td style="text-align: left;">保持在基准高度</td>
</tr>
<tr>
<td style="text-align: left;"><strong>偏移位置</strong></td>
<td style="text-align: left;">每增加 1 个偏移单位下降 1 格</td>
<td style="text-align: left;">逐级下降</td>
</tr>
<tr>
<td style="text-align: left;"><strong>红石线</strong></td>
<td style="text-align: left;">从主干道开始逐级下降</td>
<td style="text-align: left;">跟随阶梯布局</td>
</tr>
</tbody>
</table>
<p><strong>适用场景</strong>：</p>
<ul>
<li>🎶 大型音乐作品</li>
<li>🎨 需要突出声像分布的作品</li>
<li>🏗️ 追求视觉美感的展示项目</li>
</ul>
<p><strong>配置方法 (cil 模式 GUI 同理)</strong>：</p>
<pre><code class="language-python">'generation_mode': 'staircase'
</code></pre>
<p>如图所示：<br />
<img width="500" alt="alt text" src="file:///D:/Code/NBS-to-minecraftsave/documents/img/image-5.png" /></p>
<hr />
<h3>5.4 坐标系统详解 (普通用户无需了解，该处为开发需要用到的)</h3>
<h4>关键变量</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">变量名</th>
<th style="text-align: left;">含义</th>
<th style="text-align: left;">计算公式</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>tick_x</code></td>
<td style="text-align: left;">音符的 X 坐标</td>
<td style="text-align: left;"><code>base_x + tick × 2</code></td>
<td style="text-align: left;">每个 tick 占用 2 格 X 轴空间</td>
</tr>
<tr>
<td style="text-align: left;"><code>base_x, base_y, base_z</code></td>
<td style="text-align: left;">轨道组基准坐标</td>
<td style="text-align: left;">—</td>
<td style="text-align: left;">定义整个结构的起始位置</td>
</tr>
<tr>
<td style="text-align: left;"><code>pan_offset</code></td>
<td style="text-align: left;">声像偏移量</td>
<td style="text-align: left;"><code>panning ÷ 10</code></td>
<td style="text-align: left;">影响音符的 Z 轴位置</td>
</tr>
<tr>
<td style="text-align: left;"><code>z_pos</code></td>
<td style="text-align: left;">音符的最终 Z 坐标</td>
<td style="text-align: left;"><code>base_z + pan_offset</code></td>
<td style="text-align: left;">音符在南北方向的实际位置</td>
</tr>
</tbody>
</table>
<h4>坐标布局示意</h4>
<pre><code>X 轴(东西方向)：
  时间 → 沿着 X 轴正方向延伸
  每个 tick 占 2 格

Y 轴(高度方向)：
  base_y 是平台高度
  音符盒放置在 base_y 层

Z 轴(南北方向)：
  base_z 是主干道位置
  声像偏移沿 Z 轴展开
</code></pre>
<hr />
<h3>5.5 自定义音色和方块</h3>
<p>如果需要添加自定义音色，可以修改 <code>src/nbs2save/core/constants.py</code>：</p>
<pre><code class="language-python"># 在 INSTRUMENT_MAPPING 中添加新乐器
INSTRUMENT_MAPPING = {
    # ... 现有映射 ...
    16: &quot;custom_sound&quot;,  # 添加新乐器
}

# 在 INSTRUMENT_BLOCK_MAPPING 中添加对应的方块
INSTRUMENT_BLOCK_MAPPING = {
    # ... 现有映射 ...
    16: &quot;minecraft:diamond_block&quot;,  # 新乐器对应方块
}
</code></pre>
<blockquote>
<p>说明：<code>custom_sound</code> 是自定义的音色，<code>minecraft:diamond_block</code> 是对应的方块。<br />
本人还没了解过新版本的铜号在 NBS 里对应乐器 ID，所以需要自己琢磨下这里的 16 应该改成什么 ((</p>
</blockquote>
<hr />
<h3>5.6 配置保存和加载</h3>
<table>
<thead>
<tr>
<th style="text-align: left;">操作</th>
<th style="text-align: left;">步骤</th>
<th style="text-align: left;">文件格式</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>保存配置</strong></td>
<td style="text-align: left;">点击"保存配置"按钮 → 选择保存位置</td>
<td style="text-align: left;">JSON</td>
</tr>
<tr>
<td style="text-align: left;"><strong>加载配置</strong></td>
<td style="text-align: left;">点击"加载配置"按钮 → 选择 JSON 文件</td>
<td style="text-align: left;">JSON</td>
</tr>
<tr>
<td style="text-align: left;"><strong>自动保存</strong></td>
<td style="text-align: left;">程序自动保存最后一次配置到 <code>last_config.json</code></td>
<td style="text-align: left;">JSON</td>
</tr>
</tbody>
</table>
<blockquote>
<p>💡 <strong>提示</strong>：下次启动程序时，会自动加载 <code>last_config.json</code> 中的配置。</p>
</blockquote>
<hr />
<h2>六、输出文件使用</h2>
<h3>6.1 Schematic 文件使用</h3>
<h4>前提条件</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">项目</th>
<th style="text-align: left;">要求</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>Minecraft 版本</strong></td>
<td style="text-align: left;">Java Edition</td>
</tr>
<tr>
<td style="text-align: left;"><strong>必要模组</strong></td>
<td style="text-align: left;">WorldEdit</td>
</tr>
</tbody>
</table>
<h4>使用步骤</h4>
<ol>
<li><strong>复制文件</strong>到 WorldEdit 的 schematics 文件夹</li>
</ol>
<p><code>txt
   .minecraft/config/worldedit/schematics/</code></p>
<blockquote>
<p>这里有可能不是在这个路径，详细见 WorldEdit 的文档。</p>
</blockquote>
<ol start="2">
<li><strong>加载结构</strong>：在游戏中输入命令</li>
</ol>
<p><code>txt
   //schem load 文件名</code></p>
<ol start="3">
<li><strong>选择位置</strong>：选择一个合适的位置作为粘贴起点</li>
<li><strong>粘贴结构</strong>：</li>
</ol>
<p><code>txt
   //paste</code></p>
<hr />
<h3>6.2 Mcfunction 文件使用</h3>
<h4>步骤 1：创建数据包文件夹结构</h4>
<pre><code class="language-txt">save/你的存档名/datapacks/你的数据包名/
├── pack.mcmeta
└── data/你的命名空间/
    └── functions/
        └── 文件名.mcfunction
</code></pre>
<h4>步骤 2：创建 <code>pack.mcmeta</code> 文件</h4>
<pre><code class="language-json">{
  &quot;pack&quot;: {
    &quot;pack_format&quot;: 18,
    &quot;description&quot;: &quot;NBS 音乐数据包&quot;
  }
}
</code></pre>
<blockquote>
<p>⚠️ <strong>注意</strong>：<code>pack_format</code> 需要对应你的 Minecraft 版本</p>
</blockquote>
<table>
<thead>
<tr>
<th style="text-align: left;">Minecraft 版本</th>
<th style="text-align: left;">pack_format</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">1.21.4</td>
<td style="text-align: left;">48</td>
</tr>
<tr>
<td style="text-align: left;">1.21.2 - 1.21.3</td>
<td style="text-align: left;">46</td>
</tr>
<tr>
<td style="text-align: left;">1.21 - 1.21.1</td>
<td style="text-align: left;">42</td>
</tr>
<tr>
<td style="text-align: left;">1.20.5 - 1.20.6</td>
<td style="text-align: left;">32</td>
</tr>
<tr>
<td style="text-align: left;">1.20.3 - 1.20.4</td>
<td style="text-align: left;">26</td>
</tr>
<tr>
<td style="text-align: left;">1.20.2</td>
<td style="text-align: left;">18</td>
</tr>
<tr>
<td style="text-align: left;">1.20 - 1.20.1</td>
<td style="text-align: left;">15</td>
</tr>
</tbody>
</table>
<blockquote>
<p>这里使用了 AI 生成的表格，可能不是完全准确的。</p>
</blockquote>
<h4>步骤 3：放置文件</h4>
<p>将生成的 <code>.mcfunction</code> 文件放入 <code>functions</code> 文件夹。</p>
<h4>步骤 4：重新加载数据包</h4>
<p>在游戏中输入命令：</p>
<pre><code class="language-txt">/reload
</code></pre>
<h4>步骤 5：执行音乐函数</h4>
<pre><code class="language-txt">/function 命名空间：文件名
</code></pre>
<p><strong>示例</strong>：</p>
<pre><code class="language-txt">/function mymusic:test
</code></pre>
<hr />
<h2>七、故障排除</h2>
<h3>7.1 常见问题</h3>
<h4>问题 1：导入模块错误</h4>
<p><strong>错误信息</strong>：</p>
<pre><code class="language-ansi">ModuleNotFoundError: No module named 'pynbs'
</code></pre>
<p><strong>原因分析</strong>：</p>
<p>Python 依赖库未安装或安装不完整。</p>
<p><strong>解决方法</strong>：</p>
<pre><code class="language-sh">uv sync
</code></pre>
<hr />
<h4>问题 2：NBS 文件路径错误</h4>
<p><strong>错误信息</strong>：</p>
<pre><code class="language-ansi">FileNotFoundError: [Errno 2] No such file or directory: 'test.nbs'
</code></pre>
<p><strong>原因分析</strong>：</p>
<p>程序无法找到指定的 NBS 文件。</p>
<p><strong>解决方法</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">检查项</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">✅ 路径正确性</td>
<td style="text-align: left;">确保 NBS 文件路径正确</td>
</tr>
<tr>
<td style="text-align: left;">✅ 使用绝对路径</td>
<td style="text-align: left;">优先使用绝对路径而不是相对路径</td>
</tr>
<tr>
<td style="text-align: left;">✅ 文件扩展名</td>
<td style="text-align: left;">检查文件扩展名是否为 <code>.nbs</code></td>
</tr>
</tbody>
</table>
<hr />
<h4>问题 3：位置冲突错误</h4>
<p><strong>错误信息</strong>：</p>
<pre><code class="language-ansi">Exception: 位置冲突! Tick XXX, Z=XX 位置已有音符
</code></pre>
<p><strong>原因分析</strong>：</p>
<p>同一时间点，同一 Z 轴位置有多个音符。</p>
<p><strong>解决方法</strong>：</p>
<ol>
<li>在 NBS 编辑器中检查冲突的音符</li>
<li>调整冲突音符的声像 (Panning) 值</li>
<li>将冲突的轨道分配到不同的轨道组</li>
</ol>
<hr />
<h4>问题 4：配置缺失错误</h4>
<p><strong>错误信息</strong>：</p>
<pre><code class="language-ansi">ValueError: 配置缺失: output_file
</code></pre>
<p><strong>原因分析</strong>：</p>
<p>配置文件中缺少必需的配置项。</p>
<p><strong>解决方法</strong>：</p>
<p>检查 <code>config.py</code> 中的 <code>GENERATE_CONFIG</code> 是否包含所有必需字段：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">必需字段</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>data_version</code></td>
<td style="text-align: left;">Minecraft 版本</td>
</tr>
<tr>
<td style="text-align: left;"><code>input_file</code></td>
<td style="text-align: left;">NBS 文件路径</td>
</tr>
<tr>
<td style="text-align: left;"><code>type</code></td>
<td style="text-align: left;">输出格式</td>
</tr>
<tr>
<td style="text-align: left;"><code>output_file</code></td>
<td style="text-align: left;">输出文件名</td>
</tr>
</tbody>
</table>
<hr />
<h4>问题 5：GUI 启动失败</h4>
<p><strong>错误信息</strong>：</p>
<pre><code class="language-ansi">ModuleNotFoundError: No module named 'PyQt6'
</code></pre>
<p><strong>原因分析</strong>：</p>
<p>图形界面依赖库未安装。</p>
<p><strong>解决方法</strong>：</p>
<pre><code class="language-sh">uv pip install PyQt6
</code></pre>
<hr />
<h4>问题 6：Schematic 文件在游戏中无法加载</h4>
<p><strong>可能原因</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">原因</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">🔴 版本不匹配</td>
<td style="text-align: left;">Minecraft 版本与 schematic 版本不一致</td>
</tr>
<tr>
<td style="text-align: left;">🔴 模组不兼容</td>
<td style="text-align: left;">WorldEdit 版本与 Minecraft 版本不兼容</td>
</tr>
</tbody>
</table>
<p><strong>解决方法</strong>：</p>
<ol>
<li>确认 <code>data_version</code> 与你的 Minecraft 版本一致</li>
<li>更新 WorldEdit 到最新版本</li>
<li>尝试使用较低的 Minecraft 版本重新生成</li>
</ol>
<hr />
<h4>问题 7：生成的音乐播放不正常</h4>
<p><strong>可能原因</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">原因</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">🔴 不支持的乐器</td>
<td style="text-align: left;">NBS 文件中使用了程序不支持的乐器</td>
</tr>
<tr>
<td style="text-align: left;">🔴 音高超出范围</td>
<td style="text-align: left;">音符音高超出 Minecraft 支持范围</td>
</tr>
</tbody>
</table>
<p><strong>解决方法</strong>：</p>
<ol>
<li>检查 NBS 文件使用的乐器是否在支持范围内 (ID <code>0-15</code>)</li>
<li>确保音符的 MIDI 键值在 <code>33-57</code> 范围内</li>
<li>尝试在 NBS 编辑器中调整不兼容的音符</li>
</ol>
<hr />
<h3>7.2 性能优化</h3>
<h4>场景 A：大型音乐文件生成缓慢</h4>
<p><strong>原因</strong>：程序逐个音符生成，大型文件需要较长时间。</p>
<p><strong>解决方法</strong>：</p>
<table>
<thead>
<tr>
<th style="text-align: left;">方法</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">🚀 使用 schematic 格式</td>
<td style="text-align: left;">生成速度比 mcfunction 更快</td>
</tr>
<tr>
<td style="text-align: left;">⏳ 耐心等待</td>
<td style="text-align: left;">生成过程中可以查看进度条</td>
</tr>
<tr>
<td style="text-align: left;">💻 确保性能</td>
<td style="text-align: left;">关闭其他占用资源的程序</td>
</tr>
</tbody>
</table>
<hr />
<h4>场景 B：内存占用过高</h4>
<p><strong>解决方法</strong>：</p>
<ul>
<li>将大型音乐分割成多个部分</li>
<li>使用多个轨道组分散处理</li>
<li>关闭其他占用内存的程序</li>
</ul>
<hr />
<h3>7.3 日志分析</h3>
<h4>日志示例</h4>
<pre><code class="language-ansi">&gt;&gt; 处理轨道组 0:
├─ 包含轨道: [0, 1, 2, 3, 4, 5, 6]
├─ 基准坐标: (0, 64, 0)
├─ 方块配置: {'base': 'minecraft:iron_block', 'cover': 'minecraft:iron_block'}
└─ 生成模式: default
   ├─ 发现音符数量: 1234
   └─ 组内最大tick: 500
</code></pre>
<h4>日志解读</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">日志标识</th>
<th style="text-align: left;">含义</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>&gt;&gt;</code></td>
<td style="text-align: left;">开始处理新的轨道组</td>
</tr>
<tr>
<td style="text-align: left;"><code>├─</code> 和 <code>└─</code></td>
<td style="text-align: left;">显示配置信息层级</td>
</tr>
<tr>
<td style="text-align: left;"><code>发现音符数量</code></td>
<td style="text-align: left;">该组中找到的音符总数</td>
</tr>
<tr>
<td style="text-align: left;"><code>组内最大tick</code></td>
<td style="text-align: left;">音乐的长度 (以 tick 为单位)</td>
</tr>
<tr>
<td style="text-align: left;">进度条</td>
<td style="text-align: left;">整体转换进度 (0-100%)</td>
</tr>
</tbody>
</table>
<hr />
<h2>八、注意事项</h2>
<h3>8.1 许可和使用限制</h3>
<blockquote>
<p>⚠️ <strong>重要声明</strong></p>
</blockquote>
<table>
<thead>
<tr>
<th style="text-align: left;">限制类型</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">🚫 <strong>花之舞限制</strong></td>
<td style="text-align: left;"><strong>严禁</strong>使用本程序生成与《花之舞》(Flower Dance) 有关的文件，如需使用请联系作者获取授权</td>
</tr>
<tr>
<td style="text-align: left;">🚫 <strong>商业用途</strong></td>
<td style="text-align: left;"><strong>严禁</strong>将本程序用于商业用途 (如有需要需获得授权)</td>
</tr>
<tr>
<td style="text-align: left;">📝 <strong>发布要求</strong></td>
<td style="text-align: left;">使用本程序生成的作品发布到视频平台时，<strong>必须在视频简介中标注使用本程序生成</strong></td>
</tr>
</tbody>
</table>
<hr />
<h3>8.2 使用建议</h3>
<h4>备份存档</h4>
<blockquote>
<p>⚠️ <strong>重要</strong>：使用本程序前，请务必备份你的 Minecraft 存档！</p>
</blockquote>
<p>备份路径：<code>.minecraft/saves/你的存档名</code></p>
<p>将存档文件夹复制到安全位置。</p>
<hr />
<h4>合理设置坐标</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">建议</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">📍 Y 坐标</td>
<td style="text-align: left;">建议设置在 <code>64</code> 或更高，避免生成在地底</td>
</tr>
<tr>
<td style="text-align: left;">📏 轨道组间距</td>
<td style="text-align: left;">多个轨道组之间保持足够距离，避免结构重叠</td>
</tr>
<tr>
<td style="text-align: left;">🎯 可视化设置</td>
<td style="text-align: left;">使用坐标规划器可视化设置位置</td>
</tr>
</tbody>
</table>
<hr />
<h4>测试后再部署</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">步骤</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">1️⃣ 测试世界</td>
<td style="text-align: left;">先在测试世界或备份世界中测试生成的结构</td>
</tr>
<tr>
<td style="text-align: left;">2️⃣ 确认效果</td>
<td style="text-align: left;">确认播放效果无误后再部署到正式存档</td>
</tr>
<tr>
<td style="text-align: left;">3️⃣ 分段测试</td>
<td style="text-align: left;">对于大型音乐，建议分段测试</td>
</tr>
</tbody>
</table>
<hr />
<h4>选择合适的格式</h4>
<table>
<thead>
<tr>
<th style="text-align: left;">格式</th>
<th style="text-align: left;">✅ 优点</th>
<th style="text-align: left;">❌ 缺点</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>Schematic</strong></td>
<td style="text-align: left;">生成快、导入方便、可预览和调整</td>
<td style="text-align: left;">需要 WorldEdit 模组</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Mcfunction</strong></td>
<td style="text-align: left;">原版支持、无需模组</td>
<td style="text-align: left;">生成较慢、修改不便</td>
</tr>
</tbody>
</table>
<hr />
<h3>8.3 技术限制</h3>
<table>
<thead>
<tr>
<th style="text-align: left;">限制项</th>
<th style="text-align: left;">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">🔊 轨道声像</td>
<td style="text-align: left;">无法识别 NBS 中整个轨道的声像偏移，只能识别单个音符的声像</td>
</tr>
<tr>
<td style="text-align: left;">🎵 音高范围</td>
<td style="text-align: left;">Minecraft 音符盒支持的音高范围为 <code>0-24</code>(对应 MIDI 键值 <code>33-57</code>)</td>
</tr>
<tr>
<td style="text-align: left;">⚠️ 位置冲突</td>
<td style="text-align: left;">同一时间点同一 Z 轴位置不能有多个音符</td>
</tr>
<tr>
<td style="text-align: left;">⏱️ 文件大小</td>
<td style="text-align: left;">超大型音乐文件可能需要较长时间生成</td>
</tr>
</tbody>
</table>
<hr />
<blockquote>
<p>该文档部分内容使用了 AI 生成，但所有内容都经过了手动修改和人工审核，确保了文档的质量准确性和可靠性。<br />
🎵 <strong>祝你使用愉快！</strong></p>
</blockquote>
"""
