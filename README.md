# notion-cli

Notion API를 JSON으로 내보내는 CLI. AI 에이전트가 Notion 데이터를 읽고 쓸 수 있게 만든다.

## Install

```bash
pip install git+https://github.com/tellang/notion-cli.git
```

## Auth

[Notion Integrations](https://www.notion.so/profile/integrations)에서 Internal Integration을 만들고 토큰을 설정한다.

```bash
export NOTION_TOKEN=ntn_...
```

Notion 앱에서 사용할 페이지/DB에 Integration을 연결해야 한다 (페이지 우측 상단 `···` > Add connections).

## Commands

### Search

```bash
notion search "데이트" --type db --limit 5
```

### Page

```bash
notion page get <page-id>
notion page get <page-id> --props "Name,Score"
notion page create --title "새 페이지" --parent-db <db-id> --body "본문 텍스트"
notion page update <page-id> --props-json '{"Status": {"select": {"name": "Done"}}}'
notion page update <page-id> --archive true
```

### Database

```bash
notion db schema <db-id>
notion db query <db-id> --limit 10
notion db query <db-id> --filter '{"property": "Status", "select": {"equals": "Done"}}'
notion db query <db-id> --sort "Date:descending" --props "Name,Date,Score"
```

### Block

```bash
notion block list <page-id>
notion block get <block-id>
notion block append <page-id> --body "추가할 텍스트"
notion block append <page-id> --blocks-json '[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"hello"}}]}}]'
notion block delete <block-id>
```

### Comment

```bash
notion comment list <page-id>
notion comment create --page-id <page-id> --body "댓글 내용"
```

### User

```bash
notion user list
notion user me
```

## Output

모든 커맨드는 JSON을 stdout으로 출력한다. 에러도 JSON으로 stderr에 출력된다.

```json
{"error": "object_not_found", "status": 404, "message": "..."}
```

파이프라인 예시:

```bash
notion db query <db-id> | jq '.[].Name'
notion search "프로젝트" | jq '.[] | select(.object == "page")'
```

## Requirements

- Python >= 3.11
- `NOTION_TOKEN` 환경변수

## License

MIT
