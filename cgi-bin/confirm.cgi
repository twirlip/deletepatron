#!/usr/bin/perl
# confirm.cgi - retrieve patron info, check for activity, and confirm that we want to delete 'em
use FindBin;
use lib "$FindBin::Bin/..";
#use lib '/openils/lib/perl5';
use CGI qw/:standard/;
use HTML::Template;
use Sitka::Session;
use Sitka::Patron;
use Data::Dumper;

my $cgi = CGI->new;
my $session = Sitka::Session->new;

print $cgi->header,
      $cgi->start_html( -title => 'Sitka Patron Deletions - Confirm Deletions',
                        -style => { -src => "style.css" },
                      ),
      $cgi->h1('Confirm Deletions');

# check for authorization (i.e. see if user has a valid cookie)
# NB: we need to ensure that this cookie is valid specifically for patron deletions
# (can't just accept any cookie on the given domain)
my $ckey = $cgi->param('ckey'); 
$session->retrieve_session($ckey);

$session->login() unless $session->{authtoken};

# Message codes:
# OK                 => Patron can be deleted.
# INVALID_BARCODE    => Barcode entered by user is in an invalid format.
# FAIL_NOT_FOUND     => Patron does not exist or does not belong to this library.
# FAIL_ACTIVE_XACTS  => Patron has active circulations or holds.
# FAIL_HAS_FINES     => Patron owes more than $0 in fines.

my $ou = $session->{ou} || 0; # set this to authenticated user's OU? or more complex for multibranch?
my $staff = $session->{staff};

my %patrons; 
my @cannot_delete;
my @usr_is_active;
my @not_found;
my @invalid;

# ignore the existing session type, if any, and use the type from CGI params
# (i.e. if the DELETE_CARD box was checked on input.cgi, use DELETE_CARD as our session type)
$session->{session_type} = undef;
$session->type( $cgi->param('session_type') );

if (param()) {
  die('No org unit specified.') unless ($ou);
  my @barcodes = clean_and_validate($cgi->param('barcodes'));
  while (@barcodes) {
    my $barcode = shift @barcodes;
    my $patron = Sitka::Patron->new($barcode, $ou);
    if ($patron->retrieve($session->{authtoken})) {
      if ($session->check_perms($staff->{usr_id}, $patron->{ou})) {
        if ($session->type eq 'DELETE_CARD') {
          $patron->check_primary_card();
        } elsif ($session->type eq 'DELETE_PATRON') {
          $patron->check_activity();
          $patron->check_fines();
        }
        $patrons{$patron->barcode} = $patron;
        push @usr_is_active, $barcode if (grep { $_ =~ /FAIL/ } @{$patron->msgs});
      } else {
        push @cannot_delete, $barcode;
      }
    } else {
      push @not_found, $barcode;
    }
  }
}

# store patron info in session for future use (specifically, reporting on what has been deleted)
$session->{cannot_delete} = \@cannot_delete;
$session->{usr_is_active} = \@usr_is_active;
$session->{patrons} = \%patrons;
$session->{not_found} = \@not_found;
$session->{invalid} = \@invalid;
$session->save_session();

print $cgi->h2('To Be Deleted');

if (!%patrons) {

  print $cgi->p('Nothing to delete.');

} else {

  # form to confirm deletions (action="delete.cgi") based on results of the above checks
  print $cgi->start_form( -method => 'POST', -action => 'delete.cgi' );

  my $rows; # array reference for patron data to be used by HTML::Template
  while (my ($barcode, $patron) = each (%patrons)) {
    my @msgs;
    my $checkbox = 'checked';
    if ( grep {'FAIL_ACTIVE_XACTS' eq $_} @{$patron->msgs} ) {
      push @msgs, 'Patron has ' . ($patron->circs || '0') . ' active circulations and ' . ($patron->holds || '0') . ' active holds.';
      $checkbox = 'disabled';
    }
    if ( grep {'FAIL_HAS_FINES' eq $_} @{$patron->msgs} ) {
      push @msgs, 'Patron has $' . $patron->fines . ' in unpaid fines.';
      undef $checkbox unless ($checkbox eq 'disabled');
    }
    if ( grep {'FAIL_PRIMARY_CARD' eq $_} @{$patron->msgs} ) {
      push @msgs, 'This is the patron\'s primary card.  Please give the patron a new card before deleting this one.';
      $checkbox = 'disabled';
    }

    # TODO: eliminate HTML gobbledygook below
    $ready = 'Ready to delete';
    $ready .= ' this card.' if ($session->type eq 'DELETE_CARD');
    $ready .= ' this patron.' if ($session->type eq 'DELETE_PATRON');
    push @{$rows}, {
      checkbox   => ($checkbox ? "$checkbox=\"$checkbox\"" : undef),
      barcode    => $patron->{barcode},
      patronname => join(', ', ($patron->{familyname}, $patron->{givenname})),
      msgs       => ( @msgs ? $cgi->div({-class=>'warning'}, join('<br />', @msgs)) : $cgi->div({-class=>'confirm'}, $ready) ),
    };

  }

  # print patron info with the magic of HTML::Template
  my $template = HTML::Template->new(filename => 'rows-confirm.tmpl');
  my $deletemsg = 'Use the checkboxes to indicate which ';
  $deletemsg .= 'cards' if ($session->type eq 'DELETE_CARD');
  $deletemsg .= 'patrons' if ($session->type eq 'DELETE_PATRON');
  $deletemsg .= ' you want to delete.';
  $template->param(ROWS => $rows, DELETEMSG => $deletemsg);
  print $template->output();

  $submit = 'Delete Checked Cards' if ($session->type eq 'DELETE_CARD');
  $submit = 'Delete Checked Patrons' if ($session->type eq 'DELETE_PATRON');
  print $cgi->hidden('ckey', $ckey);
  print $cgi->submit('submit', $submit),
        $cgi->end_form();
}

# list invalid barcodes and barcodes not found in system
print $cgi->h2('Cannot Delete'), $cgi->p('You do not have the correct permissions to delete the following:'), $cgi->pre( join("\n", @cannot_delete) ) if (@cannot_delete);
print $cgi->h2('Not Found'), $cgi->p('The following barcodes were not found in Evergreen:'), $cgi->pre( join("\n", @not_found) ) if (@not_found);
print $cgi->h2('Invalid Barcodes'), $cgi->p('The following barcodes were entered in an invalid format:'), $cgi->pre( join("\n", @invalid) ) if (@invalid);

print end_html;

sub clean_and_validate {
  my $input = shift;
  my @barcodes = split(/[\r\n]+/, $input);
  my @clean_barcodes;
  foreach my $barcode (@barcodes) {
    next if ($barcode =~ /^\s*$/); # discard blank lines
    $barcode =~ s/^\s+//;
    $barcode =~ s/\s+$//;
    unless ($barcode =~ /^[\w-]+$/) {
      $barcode = $cgi->escapeHTML($barcode);
      push @invalid, $barcode;
      next;
    }
    push (@clean_barcodes, $barcode);
  }
  # remove duplicate barcodes
  my %hash = map {$_ => 1} @clean_barcodes;
  my @unique_barcodes = keys %hash;
  return @unique_barcodes;
}

