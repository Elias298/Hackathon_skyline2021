import './App.css'
import './header.tsx'
import Header from './header.tsx'
function App() {
  return (
    <>
    <Header />
    <div className="app-container">
      <aside className="left-frame">
        Left Frame (20% width, full height)
      </aside>

      <section className="bottom-right-frame">
        Bottom Right Frame (80% width, 50% height)
      </section>

      <section className="top-center-frame">
        Top Center Frame (60% width, 50% height)
      </section>

      <aside className="top-right-frame">
        Top Right Frame (20% width, 50% height)
      </aside>
    </div>
    </>
  )
}

export default App
