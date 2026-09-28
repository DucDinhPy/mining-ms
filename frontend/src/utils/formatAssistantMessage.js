function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function formatInline(value) {
  const codeSegments = []
  let output = escapeHtml(value)

  output = output.replace(/`([^`\n]+)`/g, (_, code) => {
    const index = codeSegments.push(`<code>${code}</code>`) - 1
    return `\u0000CODE${index}\u0000`
  })

  output = output
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_\n]+)__/g, '<strong>$1</strong>')

  output = output.replace(/\u0000CODE(\d+)\u0000/g, (_, index) => (
    codeSegments[Number(index)]
  ))

  return output
}

function splitTableRow(line) {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '')
  return trimmed.split('|').map((cell) => cell.trim())
}

function isTableSeparator(line) {
  if (!line?.includes('|')) return false

  const cells = splitTableRow(line)
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell))
}

function getAlignment(separator) {
  if (separator.startsWith(':') && separator.endsWith(':')) return 'center'
  if (separator.endsWith(':')) return 'right'
  return 'left'
}

function renderTable(headerLine, separatorLine, bodyLines) {
  const headers = splitTableRow(headerLine)
  const separators = splitTableRow(separatorLine)
  const alignments = headers.map((_, index) => getAlignment(separators[index] ?? '---'))

  const header = headers
    .map((cell, index) => (
      `<th class="align-${alignments[index]}">${formatInline(cell)}</th>`
    ))
    .join('')

  const body = bodyLines
    .map((line) => {
      const cells = splitTableRow(line)
      const row = headers
        .map((_, index) => (
          `<td class="align-${alignments[index]}">${formatInline(cells[index] ?? '')}</td>`
        ))
        .join('')

      return `<tr>${row}</tr>`
    })
    .join('')

  return [
    '<div class="markdown-table-wrap">',
    '<table>',
    `<thead><tr>${header}</tr></thead>`,
    body ? `<tbody>${body}</tbody>` : '',
    '</table>',
    '</div>',
  ].join('')
}

export function formatAssistantMessage(content) {
  const lines = String(content ?? '').replaceAll('\r\n', '\n').split('\n')
  const blocks = []
  let paragraph = []
  let index = 0

  const flushParagraph = () => {
    if (!paragraph.length) return
    blocks.push(`<p>${paragraph.map(formatInline).join('<br>')}</p>`)
    paragraph = []
  }

  while (index < lines.length) {
    const line = lines[index]
    const trimmed = line.trim()

    if (!trimmed) {
      flushParagraph()
      index += 1
      continue
    }

    if (
      line.includes('|')
      && index + 1 < lines.length
      && isTableSeparator(lines[index + 1])
    ) {
      flushParagraph()

      const separatorLine = lines[index + 1]
      const bodyLines = []
      index += 2

      while (
        index < lines.length
        && lines[index].trim()
        && lines[index].includes('|')
      ) {
        bodyLines.push(lines[index])
        index += 1
      }

      blocks.push(renderTable(line, separatorLine, bodyLines))
      continue
    }

    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      flushParagraph()
      const level = heading[1].length
      blocks.push(`<h${level}>${formatInline(heading[2])}</h${level}>`)
      index += 1
      continue
    }

    const unorderedItem = trimmed.match(/^[-*+]\s+(.+)$/)
    if (unorderedItem) {
      flushParagraph()
      const items = []

      while (index < lines.length) {
        const match = lines[index].trim().match(/^[-*+]\s+(.+)$/)
        if (!match) break
        items.push(`<li>${formatInline(match[1])}</li>`)
        index += 1
      }

      blocks.push(`<ul>${items.join('')}</ul>`)
      continue
    }

    const orderedItem = trimmed.match(/^\d+[.)]\s+(.+)$/)
    if (orderedItem) {
      flushParagraph()
      const items = []

      while (index < lines.length) {
        const match = lines[index].trim().match(/^\d+[.)]\s+(.+)$/)
        if (!match) break
        items.push(`<li>${formatInline(match[1])}</li>`)
        index += 1
      }

      blocks.push(`<ol>${items.join('')}</ol>`)
      continue
    }

    const quote = trimmed.match(/^>\s?(.+)$/)
    if (quote) {
      flushParagraph()
      blocks.push(`<blockquote>${formatInline(quote[1])}</blockquote>`)
      index += 1
      continue
    }

    paragraph.push(line)
    index += 1
  }

  flushParagraph()
  return blocks.join('')
}
