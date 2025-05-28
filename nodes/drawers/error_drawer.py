from nodes.drawers.Drawing import Drawing


class ErrorDrawer(Drawing):

    def __init__(self, filepath, width, height, inputs):
        super().__init__(filepath, width, height)
        self.title, self.content = inputs

    def draw(self):  # Add the title in bold, centered at the top third
        self.dwg_add(self.dwg.text(
            self.title,
            insert=(self.width / 2, self.height / 3),
            text_anchor="middle",
            dominant_baseline="middle",
            font_size=10,
            font_weight="bold"
        ))

        # Handle text wrapping for the content
        if self.content:
            # Parameters for text wrapping
            max_width = self.width * 0.9  # Use 90% of width for text
            line_height = 16
            font_size = 10
            x_pos = self.width / 2
            y_start = self.height / 2

            # Split content into words
            words = self.content.split()
            lines = []
            current_line = []

            # Simple word wrapping algorithm
            for word in words:
                test_line = ' '.join(current_line + [word])
                # Estimate text width (rough approximation -
                # in real SVG you might need a more precise calculation)
                estimated_width = len(test_line) * (font_size * 0.6)

                if estimated_width <= max_width or not current_line:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]

            # Add the last line if there's any content left
            if current_line:
                lines.append(' '.join(current_line))

            # Draw each line of text
            for i, line in enumerate(lines):
                y_pos = y_start + (i * line_height)
                self.dwg_add(self.dwg.text(
                    line,
                    insert=(x_pos, y_pos),
                    text_anchor="middle",
                    font_size=font_size
                ))
