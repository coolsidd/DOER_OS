#include <gtk/gtk.h>
#include <stdlib.h>

struct ScreenState {
  int screen_num;
  GtkWidget **screens;
  GtkWidget *main_window;
};

struct BufferData {
  FILE *fp;
  GtkTextIter *iter;
  GtkTextBuffer *buffer;
  GtkWidget *next_button;
};

static gboolean delete_event(GtkWidget *widget, GdkEvent *event,
                             gpointer data) {
  gtk_main_quit();
  return FALSE;
}

static void next_screen(GtkWidget *widget, gpointer data) {
  struct ScreenState current_screen_state = *((struct ScreenState *)data);
  gtk_container_remove(
      GTK_CONTAINER(current_screen_state.main_window),
      current_screen_state.screens[current_screen_state.screen_num]);
  gtk_container_add(
      GTK_CONTAINER(current_screen_state.main_window),
      current_screen_state.screens[current_screen_state.screen_num + 1]);
  current_screen_state.screen_num++;
}

#define NUM_OF_SCREENS 3
#define NUM_OF_SCRIPTS 4

static gboolean data_ready(GIOChannel *channel, GIOCondition cond,
                           gpointer data) {
  struct BufferData buffer_data = *((struct BufferData *)data);
  FILE *fp = buffer_data.fp;
  GtkTextBuffer *buffer = buffer_data.buffer;
  GtkTextIter iter = *buffer_data.iter;
  char line[256];

  while (fgets(line, sizeof line, fp)) {
    gtk_text_buffer_get_end_iter(buffer, &iter);
    /* if (strstr(line, "setup finished") != NULL) { */
    /* } */
    gtk_text_buffer_insert(buffer, &iter, line, -1);
    /* return TRUE; */
  }
  gtk_widget_set_sensitive(buffer_data.next_button, TRUE);
  fclose(fp);
  return FALSE;
}

static void add_to_screen(GtkWidget *screen, char *name) {
  GtkWidget *hbox;
  GtkWidget *checkbox;
  hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 3);
  checkbox = gtk_check_button_new_with_label(name);
  gtk_box_pack_start(GTK_BOX(hbox), checkbox, TRUE, TRUE, 3);
  gtk_box_pack_start(GTK_BOX(screen), hbox, TRUE, TRUE, 3);
  gtk_widget_show(checkbox);
  gtk_widget_show(hbox);
}

static void list_files(char *directory, GtkWidget *screen) {
  DIR *d;
  struct dirent *dir;
  d = opendir(directory);
  if (d) {
    while ((dir = readdir(d)) != NULL) {
      if (strstr(dir->d_name, ".")) {
        continue;
      }
      add_to_screen(screen, dir->d_name);

      if (strstr(dir->d_name, "tar")) {
        printf("%s\n", dir->d_name);
      }
    }
    closedir(d);
  }
}

static void open_media_folder(GtkWidget *widget, gpointer data) {
  GtkWidget *dialog;
  GtkFileChooserAction action = GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER;
  gint res;
  GtkWidget *screen = *(GtkWidget **)data;
  dialog = gtk_file_chooser_dialog_new("Open File", NULL, action, ("_Cancel"),
                                       GTK_RESPONSE_CANCEL, ("_Open"),
                                       GTK_RESPONSE_ACCEPT, NULL);

  res = gtk_dialog_run(GTK_DIALOG(dialog));
  if (res == GTK_RESPONSE_ACCEPT) {
    char *filename;
    GtkFileChooser *chooser = GTK_FILE_CHOOSER(dialog);
    filename = gtk_file_chooser_get_filename(chooser);
    list_files(filename, screen);
    g_free(filename);
  }

  gtk_widget_destroy(dialog);
}
int main(int argc, char *argv[]) {
  GtkWidget *window;
  GtkWidget **screens;
  GtkWidget *exit_button;
  char path_to_script[256];
  screens = (GtkWidget **)malloc(NUM_OF_SCREENS * sizeof(GtkWidget **));
  gtk_init(&argc, &argv);
  if (argc != 2) {
    fprintf(stderr, "usage: post_inst path_to_bin, bin is most likely in "
                    "/home/doer/Desktop/DOER_OS/bin.\n");
    exit(1);
  } else {
    sprintf(path_to_script, "cd %s && ./run_all", argv[1]);
  }
  window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title(GTK_WINDOW(window), "Welcome to DOER");

  exit_button = gtk_button_new_with_label("Exit");
  g_signal_connect(window, "delete-event", G_CALLBACK(delete_event), NULL);
  g_signal_connect(exit_button, "clicked", G_CALLBACK(delete_event), NULL);

  gtk_container_set_border_width(GTK_CONTAINER(window), 10);
  for (int i = 0; i < NUM_OF_SCREENS; i++) {
    screens[i] = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
  }
  gtk_container_add(GTK_CONTAINER(window), screens[0]);
  struct ScreenState data_ptr;
  data_ptr.screens = screens;
  data_ptr.main_window = window;
  data_ptr.screen_num = 0;
  /* Screen 1 begins */

  GtkWidget *hbox1, *hbox2, *next_button;
  hbox1 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
  hbox2 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
  gtk_box_pack_start(GTK_BOX(screens[0]), hbox1, TRUE, TRUE, 0);
  gtk_box_pack_start(GTK_BOX(screens[0]), hbox2, FALSE, TRUE, 0);
  next_button = gtk_button_new_with_label("Next");
  GtkWidget *welcome_label =
      gtk_label_new("Welcome to the post installation script for doer");
  gtk_box_pack_start(GTK_BOX(hbox1), welcome_label, TRUE, TRUE, 3);
  gtk_box_pack_start(GTK_BOX(hbox2), exit_button, FALSE, TRUE, 3);
  gtk_box_pack_end(GTK_BOX(hbox2), next_button, FALSE, TRUE, 3);
  /* GtkWidget **data_ptr; */
  /* data_ptr = (GtkWidget **)malloc(3 * sizeof(GtkWidget **)); */
  /* data_ptr[0] = window; */
  /* data_ptr[1] = screen1; */
  /* data_ptr[2] = screen2; */

  g_signal_connect(next_button, "clicked", G_CALLBACK(next_screen), &data_ptr);
  /* g_signal_connect(next_button, "clicked", G_CALLBACK(run_scripts), pbar); */
  gtk_widget_show(exit_button);
  gtk_widget_show(next_button);
  gtk_widget_show(welcome_label);
  gtk_widget_show(hbox1);
  gtk_widget_show(hbox2);
  gtk_widget_show(screens[0]);
  /* Screen 1 ends */

  /* Screen 2 begins*/
  GtkWidget *console;
  GtkTextBuffer *buffer;
  GtkTextIter iter;
  GtkWidget *scrolled_window;
  FILE *fp = popen(path_to_script, "r");
  scrolled_window =
      gtk_scrolled_window_new(NULL, NULL); // Now create scrolled window...
  console = gtk_text_view_new();           // Create textview..
  gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scrolled_window),
                                 GTK_POLICY_AUTOMATIC, GTK_POLICY_ALWAYS);
  /* gtk_box_pack_start(GTK_BOX(scrolled_window), console, TRUE, TRUE, 0); */
  gtk_container_set_border_width(GTK_CONTAINER(scrolled_window), 10);

  gtk_container_add(GTK_CONTAINER(scrolled_window), console);
  gtk_scrolled_window_set_min_content_height(
      GTK_SCROLLED_WINDOW(scrolled_window), 100);
  buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(console));
  GIOChannel *channel = g_io_channel_unix_new(fileno(fp));
  struct BufferData buffer_data;
  buffer_data.buffer = buffer;
  buffer_data.iter = &iter;
  buffer_data.fp = fp;

  GtkWidget *next_button2, *hbox3;
  next_button2 = gtk_button_new_with_label("Next");
  hbox3 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
  struct ScreenState data_ptr2;
  data_ptr2.screens = screens;
  data_ptr2.main_window = window;
  data_ptr2.screen_num = 1;

  g_signal_connect(next_button2, "clicked", G_CALLBACK(next_screen),
                   &data_ptr2);
  buffer_data.next_button = next_button2;
  gtk_box_pack_start(GTK_BOX(hbox3), next_button2, TRUE, TRUE, 3);
  gtk_box_pack_end(GTK_BOX(screens[1]), hbox3, FALSE, TRUE, 3);

  g_io_add_watch(channel, G_IO_IN, data_ready, &buffer_data);
  gtk_box_pack_start(GTK_BOX(screens[1]), scrolled_window, TRUE, TRUE, 0);

  gtk_widget_show(console);
  gtk_widget_set_sensitive(next_button2, FALSE);
  gtk_widget_show(scrolled_window);
  gtk_widget_show(next_button2);
  gtk_widget_show(hbox3);
  gtk_widget_show_all(screens[1]);
  /* Screen 2 ends */

  /* Screen 3 starts */
  GtkWidget *select_folder_button;
  select_folder_button = gtk_button_new_with_label("Open Media Folder");
  gtk_box_pack_end(GTK_BOX(screens[2]), select_folder_button, FALSE, TRUE, 3);
  gtk_widget_show(select_folder_button);
  GtkWidget *scrolled_window2, *list_of_checkboxes;
  scrolled_window2 = gtk_scrolled_window_new(NULL, NULL);
  list_of_checkboxes = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
  gtk_container_add(GTK_CONTAINER(scrolled_window2), list_of_checkboxes);
  gtk_box_pack_start(GTK_BOX(screens[2]), scrolled_window2, TRUE, TRUE, 3);
  g_signal_connect(select_folder_button, "clicked",
                   G_CALLBACK(open_media_folder), &list_of_checkboxes);
  gtk_widget_show(list_of_checkboxes);
  gtk_widget_show(scrolled_window2);
  gtk_widget_show(screens[2]);

  /* Screen 3 ends */

  gtk_widget_show(window);

  gtk_main();

  return 0;
}
