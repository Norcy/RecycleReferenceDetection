## 需求背景
首次写 Block 代码的同学可能注意到了循环引用，可是后续其他人往 Block 添加代码时可能会忘记使用 weakSelf，如下

```objc
[self.feedAdsReporter feedAdsClickEventGetClickId:clickInfo
                                completionHandler:^(NSDictionary *result, NSError *error) {
                                    [weakSelf resetClickIdANDDstlink:result];
                                    QNBLogS(@"[BrandVideoAd][%@]",self.dstlink]);
                                }];
```

这个工具可以静态扫描出代码里类似以上的写法，目前可能会有部分误判或遗漏。

支持自定义忽略指定类型 Block，比如 `enumerateObjectsUsingBlock`、`dispatch_async`

扫描范围包括 .m/.mm，非 UTF-8 编码的文件将会被忽略

## 使用方法
```shell
python Detect.py [目录/文件名]
```

## 实现原理
Todo

## 复杂点

1. Block 嵌套

    ```objc
    [adsRequestTask loadAsync:requestId onFinish:^(QNBAdsRequestTask *task) {
        NSLog(@"111");
        self.block = ^{
            NSLog(@"222");
        });
    })
    ```
    
2. 同一行可能是上一个 Block 的结束，也是下一个 Block 的开始

    ```objc
    [adsRequestTask loadAsync:requestId onFinish:^(QNBAdsRequestTask *task) {
        NSLog(@"Success");
    } onFailed:^(QNBAdsRequestTask *task, NSError *error) {
        NSLog(@"Failed");
    }];
    ```
    