#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import os
import sys
import fileinput


func_regex="(\-|\+)\s?\(.*\).*(\:\s?\(.*\).*)?{?"
block_regex="\^\s*(\(.*\).*|\s*{)"
self_regex="(self\s+|self\.)"
weakSelf_regex="weakSelf"
ignore_regex="(enumerateKeysAndObjectsUsingBlock\:|enumerateObjectsUsingBlock\:|enumerateAttribute\:)"

allDangerFilesCount = 0;
allDangerBlocksCount = 0;

class Stack: 
    """模拟栈""" 
    def __init__(self): 
        self.items = [] 
 
    def isEmpty(self): 
        return len(self.items)==0  
 
    def push(self, item): 
        self.items.append(item) 
 
    def pop(self): 
        return self.items.pop()  
 
    def peek(self): 
        if not self.isEmpty(): 
            return self.items[len(self.items)-1] 
 
    def size(self): 
        return len(self.items) 

    def allObjects(self):
        return self.items;

    def allReversedObjects(self):
        return reversed(self.items);

class BlockCode:
    def __init__(self):
       self.startLine = -1
       self.hasSelf = False;
       self.hasWeakSelf = False;
       self.endLine = -1;
       self.leftBracketCount = 0;
       self.rightBracketCount = 0;
       self.shouldIgnore = False;

    def isDanger(self):
        return (not self.shouldIgnore) and self.hasSelf and self.hasWeakSelf

    def isValid(self):
        return self.startLine > 0;

    def isBlockEnd(self):
        return self.leftBracketCount > 0 and self.leftBracketCount == self.rightBracketCount;

    def handleLine(self, line, lineNum):
        for word in line:
            if not self.isValid():
                # 如果当前行是第一行，则需要过滤 ^ 之前的所有符号
                if word == "^":
                    self.startLine = lineNum; 
            else:
                if word == "{":
                    self.leftBracketCount += 1;
                if word == "}":
                    self.rightBracketCount += 1;
            if self.isBlockEnd():
                self.endLine = lineNum;
                break;

        # ^符号的下一个才是真正的 Block 内容，写同一行的不处理
        if self.startLine != lineNum:
            if re.findall(self_regex, line):
                self.hasSelf = True;
            if re.findall(weakSelf_regex, line):
                self.hasWeakSelf = True;
        else:
            # print(line);
            if re.findall(ignore_regex, line):
                self.shouldIgnore = True;


              
def scan_files(directory,prefixArray=None,postfixArray=None):  
    files_list=[]  
      
    for root, sub_dirs, files in os.walk(directory):  
        for special_file in files:  
            if postfixArray:
                for postfix in postfixArray:
                    if special_file.endswith(postfix):  
                        files_list.append(os.path.join(root,special_file))  
            elif prefixArray:
                for prefix in prefixArray:
                    if special_file.startswith(prefix):  
                        files_list.append(os.path.join(root,special_file))  
            else:  
                files_list.append(os.path.join(root,special_file))  
                            
    return files_list 

def left_bracket_count(line):
    count=0
    for word in line:
        if word=="{":
            count=count+1
    return count;

def right_bracket_count(line):
    count=0
    for word in line:
        if word=="}":
            count=count+1
    return count;

def handleBlock(blockObjStack, blockObj, line, line_count, allDangerBlocks):
    blockObj.handleLine(line, line_count)
    # print(blockObj.__dict__);
    if blockObj.isBlockEnd():
        # print(blockObj.__dict__);
        if blockObj.isDanger():
            # print("Block 结束：Block Range: {} -> {}".format(blockObj.startLine, blockObj.endLine));
            # print("hasSelf:{}, hasWeakSelf:{}".format(blockObj.hasSelf, blockObj.hasWeakSelf))
            allDangerBlocks.append(blockObj)
        blockObjStack.pop()

def detect_block(file_path):
    line_count=0
    isInFunction = False;
    isInBlock = False;
    functionLeftBracketCount = 0;
    functionRightBracketCount = 0;
    functionStartLine = -1;
    functionEndLine = -1;
    blockObjStack = Stack()
    allDangerBlocks = []

    with open(file_path, 'r', errors='ignore') as f:
        for line in f.readlines():
            line_count=line_count+1

            # 过滤注释
            if line.strip().startswith("//"):
                continue;

            # 判断是否在函数内
            if re.findall(func_regex, line):
                functionStartLine = line_count;
                isInFunction = True;

            if isInFunction:
                functionLeftBracketCount += left_bracket_count(line);
                functionRightBracketCount += right_bracket_count(line);

            if re.findall("}", line):
                if (isInFunction and functionLeftBracketCount == functionRightBracketCount):
                    isInFunction = False;
                    functionEndLine = line_count;
                    functionLeftBracketCount = 0;
                    functionRightBracketCount = 0;
                    # print("Function Range: {} -> {}".format(functionStartLine, functionEndLine));

            # 过滤函数外的代码
            if not isInFunction:
                continue;

            # print(line_count);

            # 优先处理现有 Blocks
            allBlocks = blockObjStack.allReversedObjects();
            for eachBlock in allBlocks:
                handleBlock(blockObjStack, eachBlock, line, line_count, allDangerBlocks)

            # 判断是否可能开始一个 Block
            if re.findall(block_regex, line):
                # print("第{}行发现 Block 了".format(line_count))
                newBlockObj = BlockCode()
                blockObjStack.push(newBlockObj);
                handleBlock(blockObjStack, newBlockObj, line, line_count, allDangerBlocks)

    return allDangerBlocks
    
def handleFile(fileName):
    global allDangerFilesCount;
    global allDangerBlocksCount;

    dangerBlocks = detect_block(fileName)
    
    if len(dangerBlocks) != 0:
        allDangerBlocksCount += len(dangerBlocks);
        allDangerFilesCount += 1;

        dangerBlocksStartLine = [];
        for blockObj in dangerBlocks:
            dangerBlocksStartLine.append(blockObj.startLine); 
        print("{}\n{}\n".format(fileName, dangerBlocksStartLine))

def main():
    global allDangerFilesCount;
    global allDangerBlocksCount;

    root_path=sys.argv[1]
    if os.path.isdir(root_path):
        for file_path in scan_files(root_path, None, [".m", ".mm"]):
            # print(file_path);
            handleFile(file_path);
    else:
        handleFile(root_path)

    print("目录{}下，一共有{}个文件可能存在循环引用，一共有{}处".format(root_path, allDangerFilesCount, allDangerBlocksCount));

main()