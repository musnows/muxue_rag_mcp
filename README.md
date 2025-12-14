# RAG MCP Tool

本项目是一个基于 Model Context Protocol (MCP) 的 RAG (检索增强生成) 工具，旨在为本地文件提供智能检索能力。本项目能够扫描指定目录下的文本文件，生成向量索引，并通过 MCP 协议提供检索服务。

## 功能特性

*   **增量索引**: 智能识别文件变更，仅对新增或修改的文件进行重新索引，提高效率。
*   **自动过滤**: 自动忽略以 `.` 开头的隐藏目录（如 `.git`, `.venv` 等）。
*   **多格式支持**: 支持常见的纯文本文件格式（.txt, .md, .json, .py, .js 等）。
*   **MCP 协议支持**: 提供标准的 MCP 工具 `search_rag` 和 `read_raw_file`，可轻松集成到 Claude Desktop 等客户端。
*   **灵活配置**: 支持自定义 LLM 服务地址、模型名称和分块策略。

## 安装

本项目需要使用 Python 3.13 或更高版本。推荐使用 `uv` 进行包管理和运行。

```bash
# 克隆仓库
git clone <repository_url>
cd rag_mcp

# 安装依赖
uv sync
```

## 配置

在项目根目录下创建 `config.yaml` 文件，参考以下格式进行配置：

```yaml
llm:
  service_type: "local"  # 或 "openai" 等
  base_url: "http://localhost:1234/v1" # LLM 服务 API 地址
  api_key: "your-api-key" # 如果需要
  timeout: 60

model:
  name: "text-embedding-qwen3-embedding-4b" # 使用的 Embedding 模型名称
  context_window: 4096
  temperature: 0.7

processing:
  chunk_count: 5 # 文本分块数量
```

## 使用说明

### 命令行工具

使用 `uv run mcp_rag_tool` 运行工具。

**1. 建立索引**

对指定目录进行索引：

```bash
uv run mcp_rag_tool --dir /path/to/your/documents
```

rag数据会存放在 `/path/to/your/documents/.muxue_rag` 目录下

**2. 启动 MCP 服务器**

启动服务器以供 MCP 客户端连接：

```bash
uv run mcp_rag_tool --serve
```

也可以指定目录启动MCP服务器：

```bash
uv run mcp_rag_tool --dir /path/to/your/documents --serve
```

用这种方式启动，`serach_rag`工具不会有`dir_path`参数，所有查询会锁定这个目录下。

注意：
- 此启动方式只用于锁定`serach_rag`工具的查询目录（即屏蔽掉`dir_path`参数），不会建立rag索引。
- 必须先执行`uv run mcp_rag_tool --dir /path/to/your/documents`建立索引，再启动mcp服务器。

**3. 其他命令**

*   **清理索引**: 删除指定目录的 RAG 数据库。
    ```bash
    uv run mcp_rag_tool --clean --dir /path/to/your/documents
    ```
*   **备份索引**: 备份 RAG 数据库到指定位置。
    ```bash
    uv run mcp_rag_tool --backup --dir /path/to/your/documents --backup-path /path/to/backup
    ```
*   **查看帮助**:
    ```bash
    uv run mcp_rag_tool --help
    ```

## MCP 客户端配置

要将此工具添加到 Claude Desktop，请编辑您的 Claude 配置文件 (macOS 上通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json`)：

```json
{
  "mcpServers": {
    "rag-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/rag_mcp",
        "run",
        "mcp_rag_tool",
        "--serve"
      ],
      "env": {
        "RAG_MCP_CONFIG": "/path/to/rag_mcp/config.yaml"
      }
    }
  }
}
```

注意：请将 `/path/to/rag_mcp` 替换为您的实际项目路径。

## 工具列表

启动服务后，将提供以下工具：

*   **search_rag**: 根据关键词在索引文档中搜索相关内容，返回内容的同时会返回改内容所在的原始文件。
*   **read_raw_file**: 读取指定文件的原始内容，方便进一步分析。
