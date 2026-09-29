import uvicorn


def main() -> None:
    uvicorn.run("game_zone_gateway.zone_api:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

