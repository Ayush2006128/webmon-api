from src.core.database import Base, engine

def main():
	confirm = input("It will delete all from Database! Contineu? (yes/NO): ")

	if confirm.lower() == "yes":
		print("Dropping all tables...")
		Base.metadata.drop_all(bind=engine)

		print("Creating all tables...")
		Base.metadata.create_all(bind=engine)

		print("Database reset successful.")

	else:
		print("Aborting...")


if __name__ == '__main__':
	main()
