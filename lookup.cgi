#!/usr/bin/perl
# lookup.cgi - retrieve patron info and check for activity
#
# TODO:
#   - generate HTML output
#   - construct webform so user can confirm patron deletions

use CGI qw/:standard/;
use Sitka::Patron;

# Message codes:
# OK                 => Patron can be deleted.
# FAIL_NOT_FOUND     => Patron does not exist or does not belong to this library.
# FAIL_ACTIVE_XACTS  => Patron has active circulations or holds.
# FAIL_HAS_FINES     => Patron owes more than $0 in fines.

$ou = 0; # set this to authenticated user's OU? or more complex for multibranch?

if (param()) {
  fail('No org unit specified.') unless ($ou);
  my @input = split(/\n/, param('barcodes'));
  my (@patrons, @not_found);
  my @barcodes = clean_and_validate(@input);
  while (@barcodes) {
    my $barcode = shift @barcodes;
    my $patron = Sitka::Patron->new($barcode);
    if ($patron->retrieve()) {
      $patron->check_activity();
      $patron->check_fines();
      push @patrons, $patron;
    } else {
      push @not_found, $patron;
    }
  }
}

sub clean_and_validate {
  my @input = @_;
  my @output;
  while (@input) {
    my $barcode = shift @input;
    # TODO: clean up and validate barcodes
    push (@output, $barcode);
  }
  # TODO: remove duplicates from output
  return @output;
}

sub fail {
  my $msg = shift;
  print $msg;
  exit;
}

