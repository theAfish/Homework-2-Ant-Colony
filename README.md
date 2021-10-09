# 太极图形课S1-作业2 蚁群算法

## 背景简介
这里是一个简单的可交互式蚁群模拟器，蚁群们在这里找吃的并搬运回家。 基本操作方式：按键“D”按下时，按住鼠标左键可绘制障碍，右键可擦除；按键“F”按下时，以同样的方式可绘制食物；按键“H”按下时可设置蚁窝位置。空格以及UI按钮均可开始。开始后蚂蚁在给定时间间隔会释放信息素，模拟中用黄色代表from_home，蓝色代表from_food。觅食蚂蚁会释放黄色信息素并追寻蓝色信息素，而回家蚂蚁则释放蓝色信息素并追寻黄色信息素。随着时间流逝，信息素会逐渐挥发。

## 成功效果展示
这里可以展示这份作业（项目）run起来后的可视化效果，可以让其他人更直观感受到你的工作

![fractal demo](./data/taichi.gif)

通过修改信息素浓度以及作用等可以整出更多酷炫效果

## 整体结构（Optional）
采用了几个class来实现：

Ant类包含蚂蚁的各种信息以及对信息素以及其他环境因素的响应函数。蚂蚁们通过将运行方向前方120°角分为左、中、右三个区域，分别计算平均信息素浓度，并决定自己下一时刻的运动方向。

Detactables类包括所有可以被蚂蚁实别的环境物体的性质，在这里为信息素、食物、障碍物。每一个Detactable都具有一个网格，通过网格数据来存储该点位置的信息素浓度、食物数量或者障碍物是否存在。

Renderer类计划包含图形是否绘制、窗口信息等。但目前没有很好的构造。

AntColony类包含全部模拟过程中所需的信息以及函数，UI的各种设定也在其中。


## 运行方式
运行main.py即可
