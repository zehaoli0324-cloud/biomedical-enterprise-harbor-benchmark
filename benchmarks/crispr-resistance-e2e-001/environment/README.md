# Environment Contract

当前目录只冻结环境接口，具体容器和数据镜像在 Stage 1 再加入。任务不能把“能访问网络并临时安装依赖”作为成功条件。

## 计划中的固定组件

- `nf-core/rnaseq`
- `nf-core/differentialabundance`
- `nf-core/crisprseq`
- `FlashFry`
- `CRISPResso2`
- `Snakemake`
- `nature-figure` / `nature-statistics` 对应的审计脚本或等价 verifier

## 环境必须记录

- 容器或 lockfile digest；
- 每个工具的版本和 commit；
- 参考基因组、注释、PAM 和脱靶数据库版本；
- CPU、内存、磁盘、运行时和重试次数；
- 输入文件的 SHA-256；
- 随机种子、过滤阈值和设计矩阵。

## Stage 1 入口

数据物化后，应在本目录补充：

```text
environment/
├── input_manifest.yaml
├── container_digest.txt
├── smoke_test.sh
└── README.md
```

`smoke_test.sh` 至少要验证样本表解析、参考版本匹配、一个 screen 子集、一个 RNA-seq 子集、一个 guide 和一个 CRISPResso2 小样本可以完成，并且重跑输出 hash 稳定。
