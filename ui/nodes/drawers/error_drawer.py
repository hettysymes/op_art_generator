from ui.nodes.drawers.Drawing import Drawing


class ErrorDrawer(Drawing):

    def __init__(self, filepath, width, height, inputs):
        super().__init__(filepath, width, height)
        self.title, self.content = inputs

    def draw(self):
        self.add_bg((255, 204, 204, 255))

        # Normalized units
        x_center = 0.5  # Since width is 1 in viewBox
        title_y = 1 / 3  # Top third in normalized coordinates
        content_y_start = 0.5  # Middle in normalized coordinates
        line_height = 0.08  # Roughly 3% of height per line
        font_size = 0.08  # Also in viewBox-relative units

        # Add the title in bold, centered at the top third
        self.dwg_add(self.dwg.text(
            self.title,
            insert=(x_center, title_y),
            text_anchor="middle",
            dominant_baseline="middle",
            font_size=font_size,
            font_weight="bold"
        ))

        # Handle text wrapping for the content
        if self.content:
            max_width = 0.9  # 90% of the viewBox width
            words = self.content.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                estimated_width = len(test_line) * (font_size * 0.6)

                if estimated_width <= max_width or not current_line:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            for i, line in enumerate(lines):
                y_pos = content_y_start + (i * line_height)
                self.dwg_add(self.dwg.text(
                    line,
                    insert=(x_center, y_pos),
                    text_anchor="middle",
                    font_size=font_size
                ))

