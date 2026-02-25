
import './header.css'

type HeaderProps = {
	appName?: string
}

export default function Header({ appName = 'NUMU Dashboard' }: HeaderProps) {
	return (
		<header className="app-header">
			<div className="header-row">
				<div className="logo-slot" aria-label="Logo">
					<img src="/mitailogo.jpg" alt="Mitai logo" className="logo-img" />
					<span className="logo-text">{appName}</span>
				</div>
				<div className="profile-slot" aria-label="Profile">
					<span className="profile-name">Welcome, Alex</span>
					<button className="profile-chip" type="button">
						<span className="profile-avatar" aria-hidden="true">A</span>
						Profile
					</button>
				</div>
			</div>
		</header>
	)
}
