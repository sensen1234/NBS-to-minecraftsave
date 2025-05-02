# NBS-to-minecraftsave
### 目前实现的功能：
- 将nbs转换为mc指令（数据包）
|- 支持左右声相偏移
|- 支持多轨道组
|- 支持偏移位置有无音符判断
|- 自由更改每个轨道组的[下垫块] [上块] [x,y,z坐标]

### 未实现的功能（未来实现）
- 生成schem文件
### 此版本修复的内容：
修复了abs(pan)>1时 红石粉的生成错误
修复了轨道无法生成空轨道的bug

use python
目前还存在很多问题，目前只会做nbs转fill setblock命令，后期会做schem
请勿喷代码，会在发released后改

使用这个项目你需要安装python pynbs
安装好后请修改schem.py里的文件路径，以及轨道层
输出的文件要自己提前建一个同名文件

输出的文件请使用一个空的数据包（见testdatapack.zip）
将数据包解压到你的save/存档/datapack里，然后将使用本程序生成的文件（后缀mcfunction）放入到functions文件夹里
使用/function test:test执行生成的文件
小白暂时勿扰（以后会出小白版）
