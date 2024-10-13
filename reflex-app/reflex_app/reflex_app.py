"""Welcome to Reflex! This file outlines the steps to create your custom app."""

import reflex as rx
from rxconfig import config


class State(rx.State):
    """The app state."""
    ...


# Component Functions
def create_image(alt_text, image_height, image_source):
    """Creates an image component with specified alt text, height, and source."""
    return rx.image(
        alt=alt_text, src=image_source, height=image_height
    )


def create_hover_link(link_text):
    """Creates a hoverable link with specified text and styling."""
    return rx.el.a(
        link_text,
        href="#",
        _hover={"color": "#111827"},
        color="#374151",
        transition_property="color, background-color, border-color, text-decoration-color, fill, stroke",
        transition_timing_function="cubic-bezier(0.4, 0, 0.2, 1)",
        transition_duration="300ms",
    )


def create_list_item(item_text):
    """Creates a list item containing a hoverable link."""
    return rx.el.li(create_hover_link(link_text=item_text))


def create_section_heading(heading_text):
    """Creates a styled section heading with specified text."""
    return rx.heading(
        heading_text,
        background_color="#1F2937",
        font_weight="600",
        padding="0.5rem",
        font_size="1.125rem",
        line_height="1.75rem",
        color="#ffffff",
        as_="h3",
    )


def create_video_iframe(video_source):
    """Creates an iframe for embedding a video with specified source."""
    return rx.el.iframe(
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
        allowfullscreen=True,
        frameborder="0",
        src=video_source,
        height="100%",
        width="100%",
    )


def create_video_container(video_source):
    """Creates a container for a video iframe with aspect ratio styling."""
    return rx.box(
        create_video_iframe(video_source=video_source),
        class_name="aspect-h-9 aspect-w-16",
    )


def create_card_title(title_text):
    """Creates a styled title for a card component."""
    return rx.heading(
        title_text,
        font_weight="600",
        margin_bottom="0.5rem",
        font_size="1.125rem",
        line_height="1.75rem",
        as_="h3",
    )


def create_card_description(description_text):
    """Creates a styled description for a card component."""
    return rx.text(
        description_text,
        color="#4B5563",
        font_size="0.875rem",
        line_height="1.25rem",
    )


def create_card_content(title_text, description_text):
    """Creates the content section of a card with title and description."""
    return rx.box(
        create_card_title(title_text=title_text),
        create_card_description(description_text=description_text),
        padding="1rem",
    )


def create_video_card(
    card_title,
    video_source,
    content_title,
    content_description,
):
    """Creates a complete video card with title, video, and description."""
    return rx.box(
        create_section_heading(heading_text=card_title),
        create_video_container(video_source=video_source),
        create_card_content(
            title_text=content_title,
            description_text=content_description,
        ),
        background_color="#ffffff",
        transition_duration="300ms",
        _hover={"transform": "scale(1.05)"},
        overflow="hidden",
        border_radius="0.5rem",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        transition_property="transform",
        transition_timing_function="cubic-bezier(0.4, 0, 0.2, 1)",
    )


def create_header():
    """Creates the header section of the page with logo and navigation."""
    return rx.flex(
        create_image(
            alt_text="Company logo",
            image_height="3rem",
            image_source="https://reflex-hosting-dev-flexgen.s3.us-west-2.amazonaws.com/replicate/c10hEO0z9NKLI9aeff9JVdplHVuA3OU9NbRavBqa2ffYZvcC/out-0.webp",
        ),
        rx.box(
            rx.list(
                create_list_item(item_text="Home"),
                create_list_item(item_text="Genres"),
                create_list_item(item_text="About"),
                display="flex",
                column_gap="1.5rem",
            )
        ),
        background_color="#E5E7EB",
        display="flex",
        align_items="center",
        justify_content="space-between",
        margin_bottom="3rem",
        padding="1rem",
        border_radius="0.5rem",
    )


def create_trending_videos_section():
    """Creates the trending music videos section with multiple video cards."""
    return rx.box(
        rx.heading(
            "Trending Music Videos",
            font_weight="700",
            margin_bottom="2rem",
            font_size="1.875rem",
            line_height="2.25rem",
            text_align="center",
            as_="h2",
        ),
        rx.box(
            create_video_card(
                card_title="Classic Rock Hits",
                video_source="https://www.youtube.com/embed/BKziBPKil8E",
                content_title="Classic Rock Hits",
                content_description="Experience the timeless energy of rock legends",
            ),
            create_video_card(
                card_title="K-Pop Sensation",
                video_source="https://www.youtube.com/embed/placeholder2",
                content_title="K-Pop Sensation",
                content_description="Dive into the colorful world of Korean pop music",
            ),
            create_video_card(
                card_title="Latin Pop Hits",
                video_source="https://www.youtube.com/embed/placeholder3",
                content_title="Latin Pop Hits",
                content_description="Feel the rhythm of chart-topping Latin music",
            ),
            create_video_card(
                card_title="Pop Collaborations",
                video_source="https://www.youtube.com/embed/placeholder4",
                content_title="Pop Collaborations",
                content_description="Watch your favorite artists team up for amazing duets",
            ),
            create_video_card(
                card_title="R&B Favorites",
                video_source="https://www.youtube.com/embed/placeholder5",
                content_title="R&B Favorites",
                content_description="Immerse yourself in smooth and soulful R&B tracks",
            ),
            create_video_card(
                card_title="EDM Anthems",
                video_source="https://www.youtube.com/embed/placeholder6",
                content_title="EDM Anthems",
                content_description="Experience the electrifying beats of EDM music",
            ),
            gap="2rem",
            display="grid",
            grid_template_columns=rx.breakpoints(
                {
                    "0px": "repeat(1, minmax(0, 1fr))",
                    "768px": "repeat(2, minmax(0, 1fr))",
                    "1024px": "repeat(3, minmax(0, 1fr))",
                }
            ),
        ),
    )


def create_footer():
    """Creates the footer section with technology logos and copyright information."""
    return rx.box(
        rx.text(
            "Powered by cutting-edge technology",
            font_weight="600",
            margin_bottom="1rem",
            font_size="1.125rem",
            line_height="1.75rem",
        ),
        rx.flex(
            create_image(
                alt_text="Web development tool logo",
                image_height="2rem",
                image_source="https://reflex-hosting-dev-flexgen.s3.us-west-2.amazonaws.com/replicate/1fq2crHiPF1RY6eEDKbKK1SXMd7MfKGwedGoINMNg3TwuJZOB/out-0.webp",
            ),
            create_image(
                alt_text="Design software logo",
                image_height="2rem",
                image_source="https://reflex-hosting-dev-flexgen.s3.us-west-2.amazonaws.com/replicate/kR4mbJHPIXqBEhNE5Lo2KGUMv8NdrfefYsA98wk9DQEZ3kMnA/out-0.webp",
            ),
            create_image(
                alt_text="Video hosting platform logo",
                image_height="2rem",
                image_source="https://reflex-hosting-dev-flexgen.s3.us-west-2.amazonaws.com/replicate/nWbkyyfXFvTcL6c7Qj7n765kahqHzpjtzP5bY6TKfn9sbSmTA/out-0.webp",
            ),
            display="flex",
            justify_content="center",
            column_gap="1rem",
        ),
        rx.text(
            "© 2023 Music Video Hub. All rights reserved.",
            margin_top="2rem",
            color="#4B5563",
            font_size="0.875rem",
            line_height="1.25rem",
        ),
        margin_top="4rem",
        text_align="center",
    )


def create_main_content():
    """Creates the main content area of the page, including header, trending videos, and footer."""
    return rx.box(
        create_header(),
        create_trending_videos_section(),
        create_footer(),
        width="100%",
        style=rx.breakpoints(
            {
                "640px": {"max-width": "640px"},
                "768px": {"max-width": "768px"},
                "1024px": {"max-width": "1024px"},
                "1280px": {"max-width": "1280px"},
                "1536px": {"max-width": "1536px"},
            }
        ),
        margin_left="auto",
        margin_right="auto",
        padding_left="1rem",
        padding_right="1rem",
        padding_top="2rem",
        padding_bottom="2rem",
    )


def create_page_layout():
    """Creates the overall page layout, including styles and main content."""
    return rx.fragment(
        rx.script(src="https://cdn.tailwindcss.com"),
        rx.el.style(
            """
            @font-face {
                font-family: 'LucideIcons';
                src: url(https://unpkg.com/lucide-static@latest/font/Lucide.ttf) format('truetype');
            }
            """
        ),
        rx.box(
            create_main_content(),
            background_color="#F9FAFB",
            font_family='system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
            min_height="100vh",
        ),
    )


# Index Page
def index() -> rx.Component:
    """Defines the index page using the custom layout."""
    return create_page_layout()


# App Configuration
app = rx.App()
app.add_page(index)
app._compile()
