import { Link, useNavigate } from "react-router-dom";
import { useCart, useConfig } from "../context.jsx";

export function Summary({ cart }) {
  const c = useConfig().currency;
  return (
    <div className="summary">
      <div><span>Subtotal</span><span>{c}{cart.subtotal.toFixed(2)}</span></div>
      <div><span>Tax</span><span>{c}{cart.tax.toFixed(2)}</span></div>
      <div><span>Shipping</span><span>{cart.shipping ? `${c}${cart.shipping.toFixed(2)}` : "Free"}</span></div>
      <div className="total"><span>Total</span><span>{c}{cart.total.toFixed(2)}</span></div>
    </div>
  );
}

export default function Cart() {
  const cart = useCart();
  const cfg = useConfig();
  const nav = useNavigate();

  if (cart.items.length === 0)
    return <div className="card center"><h2>Your cart is empty</h2><p className="muted">Add some nutritious food to get started.</p><Link className="btn" to="/catalog">Browse the shop</Link></div>;

  return (
    <div className="layout cart-layout">
      <section className="card">
        <h2>Shopping cart</h2>
        {cart.warnings.map((w) => <div key={w} className="alert warn">⚠ {w}</div>)}
        <table className="table">
          <thead><tr><th>Item</th><th>Price</th><th>Qty</th><th>Total</th><th /></tr></thead>
          <tbody>{cart.items.map((i) => (
            <tr key={i.product_id}>
              <td><Link to={`/product/${i.product_id}`}>{i.name}</Link><div className="muted small">{Math.round(i.calories)} kcal · {Math.round(i.protein)}g protein</div></td>
              <td>{cfg.currency}{i.price.toFixed(2)}</td>
              <td className="qty">
                <button onClick={() => (i.quantity > 1 ? cart.setQty(i.product_id, i.quantity - 1) : cart.remove(i.product_id))}>−</button>
                <span>{i.quantity}</span>
                <button onClick={() => cart.setQty(i.product_id, i.quantity + 1)} disabled={i.quantity >= i.stock}>+</button>
              </td>
              <td>{cfg.currency}{i.line_total.toFixed(2)}</td>
              <td><button className="link-btn" onClick={() => cart.remove(i.product_id)}>Remove</button></td>
            </tr>
          ))}</tbody>
        </table>
      </section>
      <aside className="card">
        <h3>Order summary</h3>
        <Summary cart={cart} />
        <p className="muted small">Nutrition in cart: {cart.nutrition.calories} kcal · {cart.nutrition.protein}g protein</p>
        <button className="btn block" onClick={() => nav("/checkout")}>Proceed to checkout</button>
      </aside>
    </div>
  );
}
