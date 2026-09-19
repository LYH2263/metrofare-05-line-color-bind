export async function getJSON(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function sendJSON(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = `${r.status}`
    try { msg = JSON.parse(await r.text()).detail || msg } catch { /* keep status */ }
    throw new Error(msg)
  }
  return r.json()
}

export const postJSON = (path, body) => sendJSON('POST', path, body)
export const putJSON = (path, body) => sendJSON('PUT', path, body)
export const patchJSON = (path, body) => sendJSON('PATCH', path, body)
