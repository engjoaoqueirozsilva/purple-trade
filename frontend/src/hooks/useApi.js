import { useState, useEffect, useCallback, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

/**
 * Hook de acesso à API com suporte a polling, estados de loading/erro,
 * indicador de dados desatualizados (isStale) e timestamp da última
 * resposta válida (lastUpdated).
 *
 * Parâmetros:
 *   endpoint   — rota relativa, ex.: '/status'
 *   interval   — ms entre polls; null desativa o polling
 *   enabled    — false suspende qualquer requisição
 *   onSuccess  — callback(data) chamado após cada resposta válida
 *
 * Retorna:
 *   data        — último payload recebido (null enquanto não chega)
 *   loading     — true apenas na primeira carga (data ainda é null)
 *   error       — string da última falha, ou null se OK
 *   isStale     — true se o último ciclo de poll falhou mas ainda
 *                 há dados antigos em `data`
 *   lastUpdated — Date da última resposta válida, ou null
 *   refetch     — dispara uma requisição imediata
 */
export function useApi(
  endpoint,
  { interval = null, enabled = true, onSuccess = null } = {}
) {
  const [data, setData]               = useState(null)
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)
  const [isStale, setIsStale]         = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Ref para o callback evitar re-renders desnecessários quando o
  // componente pai passa uma arrow function inline
  const onSuccessRef = useRef(onSuccess)
  useEffect(() => { onSuccessRef.current = onSuccess }, [onSuccess])

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`)
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      const json = await res.json()

      setData(json)
      setError(null)
      setIsStale(false)
      setLastUpdated(new Date())

      if (typeof onSuccessRef.current === 'function') {
        onSuccessRef.current(json)
      }
    } catch (e) {
      setError(e.message)
      // Mantém o último dado válido mas sinaliza que está desatualizado
      setIsStale(prev => prev || data !== null)
    } finally {
      setLoading(prev => {
        // loading só fica false após a primeira resposta (sucesso ou erro)
        return false
      })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint])

  useEffect(() => {
    if (!enabled) return
    fetch_()
    if (!interval) return
    const id = setInterval(fetch_, interval)
    return () => clearInterval(id)
  }, [fetch_, interval, enabled])

  return { data, loading, error, isStale, lastUpdated, refetch: fetch_ }
}