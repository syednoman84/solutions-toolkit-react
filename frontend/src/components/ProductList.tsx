import type { Product } from '../types'

const PRODUCT_TYPES = ['Consumer_CC', 'Consumer_DAO', 'SMB_DAO', 'SMB_CC', 'SMB_LOC', 'SMB_TL']

interface Props {
  products: Product[]
  onChange: (products: Product[]) => void
}

export default function ProductList({ products, onChange }: Props) {
  const add = () => onChange([...products, { type: 'Consumer_CC', name: '' }])
  const remove = (i: number) => onChange(products.filter((_, idx) => idx !== i))
  const update = (i: number, field: keyof Product, value: string) => {
    const next = [...products]
    next[i] = { ...next[i], [field]: value }
    onChange(next)
  }

  return (
    <div className="form-group">
      <div className="products-header">
        <label>🎯 Products</label>
        <button type="button" className="add-btn" onClick={add}>➕</button>
      </div>
      {products.map((p, i) => (
        <div className="product-row" key={i}>
          <select value={p.type} onChange={e => update(i, 'type', e.target.value)}>
            {PRODUCT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <input
            placeholder="Product Name"
            value={p.name}
            onChange={e => update(i, 'name', e.target.value)}
          />
          <button type="button" className="remove-btn" onClick={() => remove(i)}>×</button>
        </div>
      ))}
    </div>
  )
}
