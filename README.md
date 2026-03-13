# 做菜助手（Python）

这是一个用 Python 写的“做菜助手”小应用：打开后有搜索框，输入菜名关键字，会展示对应的 **食材** 和 **制作步骤**。

## 运行方式（最简单）

1) 进入项目目录：

```bash
cd /Users/dimo/Desktop/self-app
```

2) 安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

3) 启动应用：

```bash
python3 -m streamlit run app.py
```

启动后会自动打开浏览器页面；如果没自动打开，终端会提示一个本地地址（Local URL）。

## 添加/修改菜谱

打开 `recipes.json`，按同样格式新增一个菜名即可，例如：

```json
{
  "新菜名": {
    "食材": ["..."],
    "步骤": ["..."]
  }
}
```

