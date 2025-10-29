"""Deprecated script kept for backwards compatibility."""


def main():  # pragma: no cover - legacy entry point
	"""Inform callers that the SQL setup script is no longer supported."""
	print("SQL lead database setup has been removed; MongoDB is now used for storage.")


if __name__ == "__main__":  # pragma: no cover - legacy entry point
	main()
