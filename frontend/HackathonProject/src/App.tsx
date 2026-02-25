import './App.css'
import Header from './header.tsx'
import Footer from './footer.tsx'
import Dashboard from './components/Dashboard'

function App() {
  return (
    <>
      <Header />
      <main className="app-main">
        <Dashboard />
      </main>
      <Footer />
    </>
  )
}

export default App
