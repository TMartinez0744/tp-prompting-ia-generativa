import sys


def read_grid(path):
    with open(path) as f:
        lines = f.read().splitlines()

    while lines and lines[-1] == "":
        lines.pop()

    return lines


def next_grid(grid):
    if not grid:
        return []

    rows = len(grid)
    cols = len(grid[0])
    new_grid = []

    for r in range(rows):
        new_row = []
        for c in range(cols):
            live_neighbors = 0

            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue

                    nr = r + dr
                    nc = c + dc

                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and grid[nr][nc] == "#"
                    ):
                        live_neighbors += 1

            if grid[r][c] == "#":
                new_row.append("#" if live_neighbors in (2, 3) else ".")
            else:
                new_row.append("#" if live_neighbors == 3 else ".")

        new_grid.append("".join(new_row))

    return new_grid


def main():
    grid = read_grid(sys.argv[1])
    generations = int(sys.argv[2])

    for _ in range(generations):
        grid = next_grid(grid)

    if grid:
        sys.stdout.write("\n".join(grid) + "\n")


if __name__ == "__main__":
    main()
