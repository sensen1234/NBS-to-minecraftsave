import pynbs

# 读取 NBS 文件
demo_song = pynbs.read('H:/文件/code/test.nbs')
length = demo_song.header.song_length

# command
x, y, z = "0", "0", "0"
x_int, y_int, z_int = (int(v) for v in (x, y, z))

x_length = x_int + length

blockdown = "iron_block"
blockup = "iron_block"

# 创建音色映射
instrument_mapping = {
    0: "harp",
    1: "bass",
    2: "basedrum",
    3: "snare",
    4: "hat",
    5: "guitar",
    6: "flute",
    7: "bell",
    8: "chime",
    9: "xylophone",
    10: "iron_xylophone",
    11: "cow_bell",
    12: "didgeridoo",
    13: "bit",
    14: "banjo",
    15: "pling",
}

# 创建方块映射
instrument_downblock_mapping = {
    0: "dirt",
    1: "oak_planks",
    2: "stone",
    3: "sand",
    4: "glass",
    5: "white_wool",
    6: "clay",
    7: "gold_block",
    8: "packed_ice",
    9: "bone_block",
    10: "iron_block",
    11: "soul_sand",
    12: "pumpkin",
    13: "emerald_block",
    14: "hay_block",
    15: "glowstone",
}
#音符盒音高
notepitch_mapping = {
        39: "6",
        38: "5",
        37: "4",
        36: "3",
        35: "2",
        34: "1",
        33: "0",
        40: "7",
        41: "8",
        42: "9",
        43: "10",
        44: "11",
        45: "12",
        46: "13",
        47: "14",
        48: "15",
        49: "16",
        50: "17",
        51: "18",
        52: "19",
        53: "20",
        54: "21",
        55: "22",
        56: "23",
        57: "24",
}
# 初始化 current_tick
current_tick = 0
i = 0
note_count = len(demo_song.notes)
layer = demo_song.notes[i].layer
# 遍历所有 tick
while current_tick <= length :
    has_note = False  # 标志是否找到第一层音符
    initial_i = i

    while i < note_count and demo_song.notes[i].tick ==current_tick:
        if demo_song.notes[i].layer == 0:#这里的0是要生成的轨道编号，0对应第一条轨道，1对应第二条，以此类推
        
        
            with open('H:/文件/code/test.mcfunction', 'a') as file:
            # 如果当前 note 存在于当前 tick，生成命令
                notetick = demo_song.notes[i].tick
                x_tick = x_int + notetick*2
                x_intdown= x_int-1
                y_intdown = y_int + -1
                #垫块，保持高度统一
                #这里精简代码删除了这个，以后可能继续用
                z_tick = z_int + notetick*2
                pitch = demo_song.notes[i].key
                timbre = demo_song.notes[i].instrument
                pan_fill=int(round(demo_song.notes[i].panning/10,0))
                z_pan=pan_fill+z_int
                #这里获取带pan的坐标，如果panfill为0，那么就和zint一样了，pan有值的话就左右坐标
                #这里保险起见，我还是用了round以防止出问题



                # 获取音色字符
                timbre_char = instrument_mapping.get(timbre, "unknown")
                # 获取下方块字符
                instrument_downblock = instrument_downblock_mapping.get(timbre, "unknown")
                pitch1 = notepitch_mapping.get(pitch, "unknown")

                # 生成命令
                commanddown=f"setblock {x_tick-1} {y_intdown} {z_int} {blockdown}"
                command1 = f"setblock {x_tick} {y_int} {z_pan} note_block[note={pitch1},instrument={timbre_char}]"
                #生成音符盒
                command2 = f"setblock {x_tick} {y_intdown} {z_pan} {instrument_downblock}"
                commands = [command2]

                # 当为沙子时自动追加屏障命令
                if instrument_downblock == "sand":
                    # 生成屏障命令（y轴位置下移一层）
                    commands.append(f"setblock {x_tick} {y_intdown-1} {z_pan} barrier")

                # 最终合并命令
                final_command = "\n".join(commands)
                #音符盒下面的垫块↑
                commandredstone= f"setblock {x_tick-1} {y_int} {z_int} repeater[delay=1,facing=west]"
                print(notetick)
                print(commanddown)
                print(command1)
                print(command2)
                print(commandredstone)

                if pan_fill != 0:
                    direction = 1 if pan_fill > 0 else -1
                    abs_pan = abs(pan_fill)
                    
                    z_end = z_pan - direction
                    commandfillpan = f"fill {x_tick} {y_int-1} {z_int} {x_tick} {y_int-1} {z_end} {blockdown}"
                    cd_setuppan = f"setblock {x_tick} {y_int} {z_int} {blockup}"
                    
                    commands = [commandfillpan, cd_setuppan]
                    
                    if abs_pan > 1:
                        start_z = z_int + direction
                        end_z = z_pan - direction
                        redstone_cmd = f"fill {x_tick} {y_int} {start_z} {x_tick} {y_int} {end_z} minecraft:redstone_wire[east=side]"
                        commands.append(redstone_cmd)
                    
                    file.write("\n".join(commands) + "\n")
                    

                layer = demo_song.notes[i].layer
                file.write(commanddown+"\n"+command1+"\n"+final_command+"\n"+commandredstone+"\n")

                    # 移动到下一个音符
                has_note = True
                break
        i += 1


            
    if not has_note:
                with open('H:/文件/code/test.mcfunction', 'a') as file:
                    x_air = x_int + current_tick*2
                    y_air = y_int + -1
                    x_air1 = x_air-1
                    y_air1= y_air-1

                    z_air = z_int + current_tick*2
                    commandfillup= f"setblock {x_air} {y_int} {z_int} {blockup}"
                    commandfilldown= f"setblock {x_air} {y_air} {z_int} {blockdown}"
                    commandredstoneair= f"setblock {x_air1} {y_int} {z_int} repeater[delay=1,facing=west]"
                    commandredstoneair1= f"setblock {x_air1} {y_air} {z_int} {blockdown}"
                    print(commandfillup)
                    print(commandfilldown)
                    print(commandredstoneair)
                    print(commandredstoneair1)
                    print("done")
                    file.write(commandfillup+"\n"+commandfilldown+"\n"+commandredstoneair+"\n"+commandredstoneair1+"\n")
                    
                    print(current_tick,"当前tick")
                    print(i,"当前i")
    while i < note_count and demo_song.notes[i].tick == current_tick:
        i += 1
    current_tick += 1
                    
                

    
            

    # 增加 current_tick
                

# 大动脉的 fill，但其实没啥用( 暂时先保留
command3 = f"fill {x} {y_int} {z} {x_length} {y} {z} {blockdown} keep"
command4 = f"fill {x} {y} {z} {x_length} {y} {z} {blockup} keep"

print(command3)
print(command4)
